import os
import json
import logging
from pathlib import Path
from typing import Dict, Optional
import pandas as pd
from tqdm import tqdm
from openai import OpenAI
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class LINACFailureClassifier:
    """Classifies LINAC failure reports using OpenAI's API."""
    
    SYSTEM_PROMPT = """
You are an expert medical engineering assistant who specializes in LINAC system troubleshooting.

Your job is to review the subject and description of LINAC failure reports and classify each report into one or more Failure Types.

Return your result in JSON format only with key: `failure_type` and value: category (or comma-separated categories) like:
{
  "failure_type": "Imaging System (KV/MV)"
}

### Failure Type Categories:

- "Beam Generation": Components responsible for creating, accelerating, and bending the initial electron beam, including the electron gun, linear accelerator, bending magnet, and RF power source (Klystron/Magnetron).
- "Collimation System": Systems that define the final shape of the radiation beam, including primary jaws, multi-leaf collimator (MLC), target carousel, and flattening filters/scattering foils.
- "Gantry Motion/Structure": The mechanical system responsible for rotating the gantry, including drive motors, bearings, position sensors (resolvers/encoders), and the structural frame.
- "Imaging System (KV/MV)": Hardware used for patient setup and verification imaging, including the kV X-ray source, kV flat-panel detector, MV electronic portal imaging device (EPID), and associated retractable arms.
- "Treatment Couch": The patient support system, including its motorized axes (longitudinal, lateral, vertical, rotation, pitch, roll), control pendants, and structural components.
- "Control Hardware": The distributed network of physical electronic controllers (Supervisor, Nodes), processing boards, and safety interlock circuit hardware managing machine operations.
- "System Networks": Communication infrastructure connecting system components, including CAN bus, Ethernet networks, HSSB, and associated wiring/connectors.
- "Cooling System": Systems managing the thermal environment of critical components, primarily the water cooling system (chiller, pumps, flow sensors) and specialized gas systems (e.g., SF6 for waveguide).
- "Power System/Distribution": Components managing the input and distribution of electrical power, including the modulator cabinet, main breakers, high-voltage circuits, uninterruptible power supply (UPS), and power conditioning.
- "Ancillary Room Systems": Supporting equipment within the treatment room, such as positioning lasers, in-room cameras (CCTV/Optical Guidance), and room monitors.
- "Safety Systems": Components specifically designed for personnel and equipment safety, such as emergency stop buttons, door interlocks, collision detection sensors, and radiation monitoring systems.
- "Operator Console/UI": User interface systems, display monitors, control pendants, and software interface components.

Each report can have multiple labels separated by comma. Your output must always be in dictionary format with key: `failure_type`.

Think carefully step by step and analyze the report content logically before classifying.
"""
    
    EXAMPLES = [
        {
            "subject": "GFIL, down",
            "description": """Customer is getting intermittent GFIL interlock and high vacuum activity in the electron gun. 6e energy will not run at selected dose rate. Inspected hot deck and cold deck in the gantry, downloaded gun controller parameters from the gun controller using boardman. Noted unusually high values for the grid voltage for all energies, and HV settings incorrect. Reprogrammed gun controller with grid and HV values from their other machine. Performed basic beam tuning for all energies, verified operation all energies. Observed site physics perform their QA procedure, site resumed treating patients.""",
            "failure_type": "Beam Generation"
        },
        {
            "subject": "MLC is failing and secondary feedback",
            "description": """Friday 6-29-2012: MLC down upon arrival, MLC fault #420220 leaf B20 trajectory deviation R/O = 66.56cm. Replaced the leaf motor, swapped the SFB PCB & Head Transceiver/Motor Driver PCB's (no help). As t/s ordered NFO parts ... SoftPot Iso Crg-B & Crg-B Motor I/C PCB. Saturday 6-30-2012: NFO parts pick-up Chicago O'Hare airport. Assembled MLC & verified original problem MLC fault #420220. Shutdown MLC power supply & rebooted Collimator Node ... then power MLC & successfully initialized. Ran MLC autocycle & successfully initialized MLC at gantry zero & 180 (multiple times). Could not successfully initialize the Y-Jaws due to Y1 over-current fault #415007. Verified both Jaw outer Limits & Inner Limits. Found during jaw initialization process that the jaws would come together physically & Y1 would draw high current. Made slight adjustment to the collision switch position & successfully initialized jaws. Completed Jaw Calibration (internal) and saved configuration.""",
            "failure_type": "Collimation System"
        },
        {
            "subject": "Installed floating monitor arms.",
            "description": """Mounted 4 Linac control monitors on the floating arms. Same configuration as Trilogy""",
            "failure_type": "Operator Console/UI"
        }
    ]
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        """
        Initialize the classifier.
        
        Args:
            api_key: OpenAI API key. If None, loads from environment.
            model: OpenAI model to use for classification.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.formatted_examples = self._format_examples()
        logger.info(f"Initialized LINACFailureClassifier with model: {model}")
    
    def _format_examples(self) -> str:
        """Format few-shot examples for the prompt."""
        template = """**Example report**
Subject: {subject}
Description: {description}
Failure Type: {failure_type}
"""
        return "\n".join([template.format(**ex) for ex in self.EXAMPLES])
    
    def classify_report(self, subject: str, description: str, max_retries: int = 3) -> Dict:
        """
        Classify a single LINAC failure report.
        
        Args:
            subject: Report subject line.
            description: Report description text.
            max_retries: Maximum number of retry attempts on failure.
            
        Returns:
            Dictionary with classification results.
        """
        user_prompt = f"""Here are the examples:
{self.formatted_examples}

Classify this report:
Failure_type must be selected exclusively from the defined Failure Type categories.

**LINAC downtime report**
Subject: {subject}
Description: {description}
"""
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7
                )
                
                result_text = response.choices[0].message.content.strip()
                
                # Try to parse JSON from the response
                # Handle markdown code blocks if present
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0].strip()
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0].strip()
                
                result = json.loads(result_text)
                return result
                
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return {"failure_type": "ParseError", "raw_response": result_text, "error": str(e)}
                    
            except Exception as e:
                logger.error(f"API call error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return {"failure_type": "APIError", "error": str(e)}
        
        return {"failure_type": "UnknownError"}
    
    def classify_dataframe(self, df: pd.DataFrame, 
                          subject_col: str = 'subject',
                          description_col: str = 'description',
                          output_col: str = 'llm_classification') -> pd.DataFrame:
        """
        Classify all reports in a DataFrame.
        
        Args:
            df: DataFrame containing reports.
            subject_col: Name of the subject column.
            description_col: Name of the description column.
            output_col: Name of the output column for results.
            
        Returns:
            DataFrame with classification results added.
        """
        logger.info(f"Starting classification of {len(df)} reports...")
        
        tqdm.pandas(desc="Classifying reports")
        df[output_col] = df.progress_apply(
            lambda row: self.classify_report(
                str(row[subject_col]), 
                str(row[description_col])
            ),
            axis=1
        )
        
        # Extract failure_type to separate column for easier analysis
        df['failure_type'] = df[output_col].apply(
            lambda x: x.get('failure_type', 'Error') if isinstance(x, dict) else 'Error'
        )
        
        logger.info("Classification complete!")
        return df


def main():
    """Main execution function."""
    # Configuration
    INPUT_FILE = Path('/Users/yeochanyoun/Desktop/projects/LINAC_prediction/clean_data/df_full_desc.csv')
    OUTPUT_FILE = Path('output/classified_reports.csv')
    
    # Create output directory if it doesn't exist
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load data
        logger.info(f"Loading data from {INPUT_FILE}...")
        df = pd.read_csv(INPUT_FILE)
        logger.info(f"Loaded {len(df)} reports")
        
        # Initialize classifier
        classifier = LINACFailureClassifier(model="gpt-4o")
        
        # Classify reports
        df_classified = classifier.classify_dataframe(df)
        
        # Save results
        logger.info(f"Saving results to {OUTPUT_FILE}...")
        df_classified.to_csv(OUTPUT_FILE, index=False)
        
        # Print summary statistics
        logger.info("\n=== Classification Summary ===")
        logger.info(f"Total reports: {len(df_classified)}")
        logger.info(f"\nFailure type distribution:")
        logger.info(df_classified['failure_type'].value_counts())
        
        # Check for errors
        error_count = df_classified['failure_type'].str.contains('Error').sum()
        if error_count > 0:
            logger.warning(f"\n⚠️  {error_count} reports had classification errors")
        
    except FileNotFoundError:
        logger.error(f"Input file not found: {INPUT_FILE}")
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)


if __name__ == "__main__":
    main()