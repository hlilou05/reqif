import PyPDF2
import re
import xml.etree.ElementTree as ET

def extract_requirements(pdf_path):
    """Extracts requirements from the given PDF file."""
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        text = "".join([page.extract_text() for page in reader.pages if page.extract_text()])
    
    # Regex pattern to capture requirements
    pattern = re.compile(r"ID: (\d+) / Legacy GUID: ([^\s]+) / CR: (\d+)\n(.*?)\n", re.DOTALL)
    
    requirements = []
    for match in pattern.finditer(text):
        req_id, legacy_guid, cr, description = match.groups()
        requirements.append({
            "D": req_id,
            "Legacy GUID": legacy_guid,
            "CR": cr,
            "description": description.strip()
        })
    return requirements

def generate_reqif(requirements, output_path):
    """Generates a .reqif file from extracted requirements."""
    reqif = ET.Element("REQ-IF")
    
    core_content = ET.SubElement(reqif, "CORE-CONTENT")
    
    for req in requirements:
        spec_object = ET.SubElement(core_content, "SPEC-OBJECT")
        ET.SubElement(spec_object, "D").text = req["D"]
        ET.SubElement(spec_object, "LegacyGUID").text = req["Legacy GUID"]
        ET.SubElement(spec_object, "CR").text = req["CR"]
        ET.SubElement(spec_object, "description").text = req["description"]
    
    tree = ET.ElementTree(reqif)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    print(f"REQIF file generated: {output_path}")

if __name__ == "__main__":
    pdf_path = "CYS.pdf"
    output_path = "output.reqif"
    
    requirements = extract_requirements(pdf_path)
    generate_reqif(requirements, output_path)
