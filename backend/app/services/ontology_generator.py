"""
Ontology generation service / Servizio di generazione ontologia.
Endpoint 1: analyze text and generate entity/relationship type definitions
for social simulation / analizza il testo e genera definizioni di tipi entita/
relazioni per simulazione sociale.
"""

import json
from typing import Dict, Any, List, Optional
from ..utils.llm_client import LLMClient


# System prompt for ontology generation / Prompt di sistema per generazione ontologia
ONTOLOGY_SYSTEM_PROMPT = """You are an expert in knowledge-graph ontology design.
Analyze the provided text and simulation requirements, then design entity and
relationship types suitable for **social-media public-opinion simulation**.

Important / Importante:
- Output must be valid JSON only.
- Do not output any extra text outside JSON.

## Core Task Context / Contesto del compito

We are building a social-media opinion simulation system. In this system:
- Each entity is a real actor/account that can post, interact and spread info.
- Entities influence each other via reposts, comments, replies, etc.
- We need to simulate reactions and information diffusion paths.

Therefore, entities must be real-world actors that can speak and interact.

Allowed examples / Esempi consentiti:
- Individuals (public figures, stakeholders, opinion leaders, experts, citizens)
- Companies and brands (including official accounts)
- Organizations (universities, associations, NGOs, unions)
- Government/regulatory bodies
- Media organizations (newspapers, TV, websites, creator media)
- Social platforms themselves
- Representative groups (alumni groups, fan communities, advocacy groups)

Not allowed / Non consentito:
- Abstract concepts (e.g., "public opinion", "emotion", "trend")
- Topics/issues (e.g., "academic integrity", "education reform")
- Pure stances (e.g., "support side", "opposition side")

## Output Format / Formato output

Return JSON with this structure:

```json
{
    "entity_types": [
        {
            "name": "Entity type name (English, PascalCase)",
            "description": "Short description (English, <=100 chars)",
            "attributes": [
                {
                    "name": "Attribute name (English, snake_case)",
                    "type": "text",
                    "description": "Attribute description"
                }
            ],
            "examples": ["example entity 1", "example entity 2"]
        }
    ],
    "edge_types": [
        {
            "name": "Relationship type name (English, UPPER_SNAKE_CASE)",
            "description": "Short description (English, <=100 chars)",
            "source_targets": [
                {"source": "source entity type", "target": "target entity type"}
            ],
            "attributes": []
        }
    ],
    "analysis_summary": "Brief analysis summary (English or Italian)"
}
```

## Design Guidelines / Linee guida

### 1) Entity Type Design (strictly required)

You must output exactly 10 entity types.

Hierarchy requirements (must include specific + fallback types):

Your 10 entity types must include:

A. Fallback types (required, place as last two):
   - `Person`: fallback for any natural person not covered by more specific person types.
   - `Organization`: fallback for any organization not covered by more specific org types.

B. Specific types (8, derived from the text):
   - Create specific classes for the major actors in the document.
   - Example (academic): `Student`, `Professor`, `University`
   - Example (business): `Company`, `CEO`, `Employee`

Why fallback types are needed:
- Text may contain many uncategorized individuals.
- If no specific type applies, map them to `Person`.
- Small/temporary groups should map to `Organization`.

Specific-type design principles:
- Identify frequent or central actor classes from the text.
- Keep type boundaries clear and non-overlapping.
- Each description should clarify how it differs from fallback types.

### 2) Relationship Type Design

- Count: 6-10 types.
- Relationships should reflect realistic social-media interactions.
- Ensure source_targets align with your entity types.

### 3) Attribute Design

- Use 1-3 key attributes per entity type.
- Do not use reserved names: `name`, `uuid`, `group_id`, `created_at`, `summary`.
- Prefer names like: `full_name`, `title`, `role`, `position`, `location`, `description`.

## Entity Type Reference

Specific person types:
- Student, Professor, Journalist, Celebrity, Executive, Official, Lawyer, Doctor

Fallback person type:
- Person: any natural person not matching specific person types

Specific organization types:
- University, Company, GovernmentAgency, MediaOutlet, Hospital, School, NGO

Fallback organization type:
- Organization: any organization not matching specific org types

## Relationship Type Reference

- WORKS_FOR, STUDIES_AT, AFFILIATED_WITH, REPRESENTS, REGULATES,
  REPORTS_ON, COMMENTS_ON, RESPONDS_TO, SUPPORTS, OPPOSES,
  COLLABORATES_WITH, COMPETES_WITH
"""


class OntologyGenerator:
    """
    Ontology generator / Generatore di ontologia.
    Analyze text and generate entity/relationship type definitions /
    Analizza testo e genera tipi entita/relazioni.
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()
    
    def generate(
        self,
        document_texts: List[str],
        simulation_requirement: str,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate ontology definition / Genera definizione ontologia.

        Args:
            document_texts: document text list / lista testi documento
            simulation_requirement: simulation requirement / requisito simulazione
            additional_context: optional extra context / contesto extra opzionale

        Returns:
            ontology dict (entity_types, edge_types, etc.) /
            dizionario ontologia (entity_types, edge_types, ecc.)
        """
        # Build user message / Costruisci messaggio utente
        user_message = self._build_user_message(
            document_texts, 
            simulation_requirement,
            additional_context
        )
        
        messages = [
            {"role": "system", "content": ONTOLOGY_SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
        
        # Call LLM / Chiama LLM
        result = self.llm_client.chat_json(
            messages=messages,
            temperature=0.3,
            max_tokens=4096
        )
        
        # Validate and post-process / Valida e post-processa
        result = self._validate_and_process(result)
        
        return result
    
    # Max text length sent to LLM.
    MAX_TEXT_LENGTH_FOR_LLM = 50000
    
    def _build_user_message(
        self,
        document_texts: List[str],
        simulation_requirement: str,
        additional_context: Optional[str]
    ) -> str:
        """Build user message / Costruisci messaggio utente."""
        
        # Merge texts / Unisci testi
        combined_text = "\n\n---\n\n".join(document_texts)
        original_length = len(combined_text)
        
        # Truncate if over limit (affects LLM input only, not graph build).
        if len(combined_text) > self.MAX_TEXT_LENGTH_FOR_LLM:
            combined_text = combined_text[:self.MAX_TEXT_LENGTH_FOR_LLM]
            combined_text += (
                f"\n\n...(original length / lunghezza originale: {original_length} chars, "
                f"truncated to first {self.MAX_TEXT_LENGTH_FOR_LLM} chars for ontology analysis)..."
            )
        
        message = f"""## Simulation Requirement / Requisito di simulazione

{simulation_requirement}

## Document Content / Contenuto documento

{combined_text}
"""
        
        if additional_context:
            message += f"""
## Additional Notes / Note aggiuntive

{additional_context}
"""
        
        message += """
Design entity and relationship types for social-opinion simulation based on the
content above.

Mandatory rules / Regole obbligatorie:
1. Output exactly 10 entity types.
2. The last 2 must be fallback types: Person and Organization.
3. The first 8 must be specific types derived from the text.
4. All entities must be real actors that can speak/interact, not abstractions.
5. Attribute names must avoid reserved words (name, uuid, group_id, etc.);
   use alternatives like full_name, org_name.
"""
        
        return message
    
    def _validate_and_process(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and post-process result / Valida e post-processa risultato."""
        
        # Ensure required fields exist.
        if "entity_types" not in result:
            result["entity_types"] = []
        if "edge_types" not in result:
            result["edge_types"] = []
        if "analysis_summary" not in result:
            result["analysis_summary"] = ""
        
        # Validate entity types.
        for entity in result["entity_types"]:
            if "attributes" not in entity:
                entity["attributes"] = []
            if "examples" not in entity:
                entity["examples"] = []
            # Ensure description length <= 100 chars.
            if len(entity.get("description", "")) > 100:
                entity["description"] = entity["description"][:97] + "..."
        
        # Validate edge types.
        for edge in result["edge_types"]:
            if "source_targets" not in edge:
                edge["source_targets"] = []
            if "attributes" not in edge:
                edge["attributes"] = []
            if len(edge.get("description", "")) > 100:
                edge["description"] = edge["description"][:97] + "..."
        
        # Zep API limits: max 10 custom entity types, max 10 custom edge types.
        MAX_ENTITY_TYPES = 10
        MAX_EDGE_TYPES = 10
        
        # Fallback type definitions.
        person_fallback = {
            "name": "Person",
            "description": "Any individual person not fitting other specific person types.",
            "attributes": [
                {"name": "full_name", "type": "text", "description": "Full name of the person"},
                {"name": "role", "type": "text", "description": "Role or occupation"}
            ],
            "examples": ["ordinary citizen", "anonymous netizen"]
        }
        
        organization_fallback = {
            "name": "Organization",
            "description": "Any organization not fitting other specific organization types.",
            "attributes": [
                {"name": "org_name", "type": "text", "description": "Name of the organization"},
                {"name": "org_type", "type": "text", "description": "Type of organization"}
            ],
            "examples": ["small business", "community group"]
        }
        
        # Check whether fallback types are already present.
        entity_names = {e["name"] for e in result["entity_types"]}
        has_person = "Person" in entity_names
        has_organization = "Organization" in entity_names
        
        # Build fallback list to add.
        fallbacks_to_add = []
        if not has_person:
            fallbacks_to_add.append(person_fallback)
        if not has_organization:
            fallbacks_to_add.append(organization_fallback)
        
        if fallbacks_to_add:
            current_count = len(result["entity_types"])
            needed_slots = len(fallbacks_to_add)
            
            # If adding fallback types exceeds 10, drop some existing types.
            if current_count + needed_slots > MAX_ENTITY_TYPES:
                # Compute number of types to remove.
                to_remove = current_count + needed_slots - MAX_ENTITY_TYPES
                # Remove from tail, preserving earlier (usually more relevant) types.
                result["entity_types"] = result["entity_types"][:-to_remove]
            
            # Append fallback types.
            result["entity_types"].extend(fallbacks_to_add)
        
        # Final safety cap.
        if len(result["entity_types"]) > MAX_ENTITY_TYPES:
            result["entity_types"] = result["entity_types"][:MAX_ENTITY_TYPES]
        
        if len(result["edge_types"]) > MAX_EDGE_TYPES:
            result["edge_types"] = result["edge_types"][:MAX_EDGE_TYPES]
        
        return result
    
    def generate_python_code(self, ontology: Dict[str, Any]) -> str:
        """
        Convert ontology definition to Python code (similar to ontology.py) /
        Converte definizione ontologia in codice Python.

        Args:
            ontology: ontology dict / dizionario ontologia

        Returns:
            Python code string / stringa codice Python
        """
        code_lines = [
            '"""',
            'Custom entity type definitions',
            'Auto-generated by MiroFish for social-opinion simulation',
            '"""',
            '',
            'from pydantic import Field',
            'from zep_cloud.external_clients.ontology import EntityModel, EntityText, EdgeModel',
            '',
            '',
            '# ============== Entity Type Definitions ==============',
            '',
        ]
        
        # Generate entity types.
        for entity in ontology.get("entity_types", []):
            name = entity["name"]
            desc = entity.get("description", f"A {name} entity.")
            
            code_lines.append(f'class {name}(EntityModel):')
            code_lines.append(f'    """{desc}"""')
            
            attrs = entity.get("attributes", [])
            if attrs:
                for attr in attrs:
                    attr_name = attr["name"]
                    attr_desc = attr.get("description", attr_name)
                    code_lines.append(f'    {attr_name}: EntityText = Field(')
                    code_lines.append(f'        description="{attr_desc}",')
                    code_lines.append(f'        default=None')
                    code_lines.append(f'    )')
            else:
                code_lines.append('    pass')
            
            code_lines.append('')
            code_lines.append('')
        
        code_lines.append('# ============== Edge Type Definitions ==============')
        code_lines.append('')
        
        # Generate edge types.
        for edge in ontology.get("edge_types", []):
            name = edge["name"]
            # Convert to PascalCase class name.
            class_name = ''.join(word.capitalize() for word in name.split('_'))
            desc = edge.get("description", f"A {name} relationship.")
            
            code_lines.append(f'class {class_name}(EdgeModel):')
            code_lines.append(f'    """{desc}"""')
            
            attrs = edge.get("attributes", [])
            if attrs:
                for attr in attrs:
                    attr_name = attr["name"]
                    attr_desc = attr.get("description", attr_name)
                    code_lines.append(f'    {attr_name}: EntityText = Field(')
                    code_lines.append(f'        description="{attr_desc}",')
                    code_lines.append(f'        default=None')
                    code_lines.append(f'    )')
            else:
                code_lines.append('    pass')
            
            code_lines.append('')
            code_lines.append('')
        
        # Generate type dictionaries.
        code_lines.append('# ============== Type Configuration ==============')
        code_lines.append('')
        code_lines.append('ENTITY_TYPES = {')
        for entity in ontology.get("entity_types", []):
            name = entity["name"]
            code_lines.append(f'    "{name}": {name},')
        code_lines.append('}')
        code_lines.append('')
        code_lines.append('EDGE_TYPES = {')
        for edge in ontology.get("edge_types", []):
            name = edge["name"]
            class_name = ''.join(word.capitalize() for word in name.split('_'))
            code_lines.append(f'    "{name}": {class_name},')
        code_lines.append('}')
        code_lines.append('')
        
        # Generate edge source_targets map.
        code_lines.append('EDGE_SOURCE_TARGETS = {')
        for edge in ontology.get("edge_types", []):
            name = edge["name"]
            source_targets = edge.get("source_targets", [])
            if source_targets:
                st_list = ', '.join([
                    f'{{"source": "{st.get("source", "Entity")}", "target": "{st.get("target", "Entity")}"}}'
                    for st in source_targets
                ])
                code_lines.append(f'    "{name}": [{st_list}],')
        code_lines.append('}')
        
        return '\n'.join(code_lines)

