"""
OASIS Reddit simulation preset script / Script preset simulazione OASIS Reddit.
This script reads configuration parameters to execute simulations automatically /
Questo script legge i parametri di configurazione per eseguire simulazioni in modo automatico.

Features / Funzionalita:
- Keep environment open after simulation and wait for commands /
    Mantiene l'ambiente aperto dopo la simulazione e attende comandi
- Supports IPC Interview commands / Supporta comandi Interview via IPC
- Supports single-agent and batch interviews / Supporta interviste singole e batch
- Supports remote environment shutdown command / Supporta comando remoto di chiusura ambiente

Usage / Utilizzo:
        python run_reddit_simulation.py --config /path/to/simulation_config.json
        python run_reddit_simulation.py --config /path/to/simulation_config.json --no-wait  # close immediately / chiudi subito
"""

import argparse
import asyncio
import json
import logging
import os
import random
import signal
import sys
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional

# Global variables for signal handling / Variabili globali per gestione segnali
_shutdown_event = None
_cleanup_done = False

# Add project paths / Aggiungi path progetto
_scripts_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.abspath(os.path.join(_scripts_dir, '..'))
_project_root = os.path.abspath(os.path.join(_backend_dir, '..'))
sys.path.insert(0, _scripts_dir)
sys.path.insert(0, _backend_dir)

# Load project-root .env file (including LLM_API_KEY and related settings) /
# Carica file .env dalla root progetto (inclusi LLM_API_KEY e impostazioni correlate)
from dotenv import load_dotenv
_env_file = os.path.join(_project_root, '.env')
if os.path.exists(_env_file):
    load_dotenv(_env_file)
else:
    _backend_env = os.path.join(_backend_dir, '.env')
    if os.path.exists(_backend_env):
        load_dotenv(_backend_env)


import re


class UnicodeFormatter(logging.Formatter):
    """Custom formatter for Unicode escapes / Formattatore custom per escape Unicode."""
    
    UNICODE_ESCAPE_PATTERN = re.compile(r'\\u([0-9a-fA-F]{4})')
    
    def format(self, record):
        result = super().format(record)
        
        def replace_unicode(match):
            try:
                return chr(int(match.group(1), 16))
            except (ValueError, OverflowError):
                return match.group(0)
        
        return self.UNICODE_ESCAPE_PATTERN.sub(replace_unicode, result)


class MaxTokensWarningFilter(logging.Filter):
    """Filter camel-ai max_tokens warnings / Filtra warning camel-ai su max_tokens."""
    
    def filter(self, record):
        # Filter max_tokens warning logs / Filtra log di warning max_tokens
        if "max_tokens" in record.getMessage() and "Invalid or missing" in record.getMessage():
            return False
        return True


# Add filter at module load so it applies before camel executes /
# Aggiunge filtro al caricamento modulo prima dell'esecuzione camel
logging.getLogger().addFilter(MaxTokensWarningFilter())


def setup_oasis_logging(log_dir: str):
    """Configure OASIS logs with fixed filenames / Configura log OASIS con nomi fissi."""
    os.makedirs(log_dir, exist_ok=True)
    
    # Cleanup old log files / Pulisce file log precedenti
    for f in os.listdir(log_dir):
        old_log = os.path.join(log_dir, f)
        if os.path.isfile(old_log) and f.endswith('.log'):
            try:
                os.remove(old_log)
            except OSError:
                pass
    
    formatter = UnicodeFormatter("%(levelname)s - %(asctime)s - %(name)s - %(message)s")
    
    loggers_config = {
        "social.agent": os.path.join(log_dir, "social.agent.log"),
        "social.twitter": os.path.join(log_dir, "social.twitter.log"),
        "social.rec": os.path.join(log_dir, "social.rec.log"),
        "oasis.env": os.path.join(log_dir, "oasis.env.log"),
        "table": os.path.join(log_dir, "table.log"),
    }
    
    for logger_name, log_file in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        logger.handlers.clear()
        file_handler = logging.FileHandler(log_file, encoding='utf-8', mode='w')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.propagate = False


try:
    from camel.models import ModelFactory
    from camel.types import ModelPlatformType
    import oasis
    from oasis import (
        ActionType,
        LLMAction,
        ManualAction,
        generate_reddit_agent_graph
    )
except ImportError as e:
    print(f"Error: missing dependency / Errore: dipendenza mancante {e}")
    print("Please install first / Installa prima: pip install oasis-ai camel-ai")
    sys.exit(1)


# IPC constants / Costanti IPC
IPC_COMMANDS_DIR = "ipc_commands"
IPC_RESPONSES_DIR = "ipc_responses"
ENV_STATUS_FILE = "env_status.json"

class CommandType:
    """Command type constants / Costanti tipo comando."""
    INTERVIEW = "interview"
    BATCH_INTERVIEW = "batch_interview"
    CLOSE_ENV = "close_env"


class IPCHandler:
    """IPC command handler / Gestore comandi IPC."""
    
    def __init__(self, simulation_dir: str, env, agent_graph):
        self.simulation_dir = simulation_dir
        self.env = env
        self.agent_graph = agent_graph
        self.commands_dir = os.path.join(simulation_dir, IPC_COMMANDS_DIR)
        self.responses_dir = os.path.join(simulation_dir, IPC_RESPONSES_DIR)
        self.status_file = os.path.join(simulation_dir, ENV_STATUS_FILE)
        self._running = True
        
        # Ensure directories exist / Assicura esistenza directory
        os.makedirs(self.commands_dir, exist_ok=True)
        os.makedirs(self.responses_dir, exist_ok=True)
    
    def update_status(self, status: str):
        """Update environment status / Aggiorna stato ambiente."""
        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump({
                "status": status,
                "timestamp": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
    
    def poll_command(self) -> Optional[Dict[str, Any]]:
        """Poll pending commands / Esegue polling comandi in attesa."""
        if not os.path.exists(self.commands_dir):
            return None
        
        # Collect command files sorted by time / Raccoglie file comando ordinati per tempo
        command_files = []
        for filename in os.listdir(self.commands_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.commands_dir, filename)
                command_files.append((filepath, os.path.getmtime(filepath)))
        
        command_files.sort(key=lambda x: x[1])
        
        for filepath, _ in command_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                continue
        
        return None
    
    def send_response(self, command_id: str, status: str, result: Dict = None, error: str = None):
        """Send response / Invia risposta."""
        response = {
            "command_id": command_id,
            "status": status,
            "result": result,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        
        response_file = os.path.join(self.responses_dir, f"{command_id}.json")
        with open(response_file, 'w', encoding='utf-8') as f:
            json.dump(response, f, ensure_ascii=False, indent=2)
        
        # Remove command file / Rimuove file comando
        command_file = os.path.join(self.commands_dir, f"{command_id}.json")
        try:
            os.remove(command_file)
        except OSError:
            pass
    
    async def handle_interview(self, command_id: str, agent_id: int, prompt: str) -> bool:
        """
        Handle single-agent interview command / Gestisce comando interview singolo agente.
        
        Returns:
            True means success, False means failure / True successo, False fallimento
        """
        try:
            # Get agent / Ottieni agente
            agent = self.agent_graph.get_agent(agent_id)
            
            # Create Interview action / Crea azione Interview
            interview_action = ManualAction(
                action_type=ActionType.INTERVIEW,
                action_args={"prompt": prompt}
            )
            
            # Execute Interview / Esegui Interview
            actions = {agent: interview_action}
            await self.env.step(actions)
            
            # Fetch result from database / Recupera risultato dal database
            result = self._get_interview_result(agent_id)
            
            self.send_response(command_id, "completed", result=result)
            print(f"  Interview completed / completata: agent_id={agent_id}")
            return True
            
        except Exception as e:
            error_msg = str(e)
            print(f"  Interview failed / fallita: agent_id={agent_id}, error={error_msg}")
            self.send_response(command_id, "failed", error=error_msg)
            return False
    
    async def handle_batch_interview(self, command_id: str, interviews: List[Dict]) -> bool:
        """
        Handle batch interview command / Gestisce comando interview batch.
        
        Args:
            interviews: [{"agent_id": int, "prompt": str}, ...]
        """
        try:
            # Build action dictionary / Costruisci dizionario azioni
            actions = {}
            agent_prompts = {}  # Track prompt per agent / Traccia prompt per agente
            
            for interview in interviews:
                agent_id = interview.get("agent_id")
                prompt = interview.get("prompt", "")
                
                try:
                    agent = self.agent_graph.get_agent(agent_id)
                    actions[agent] = ManualAction(
                        action_type=ActionType.INTERVIEW,
                        action_args={"prompt": prompt}
                    )
                    agent_prompts[agent_id] = prompt
                except Exception as e:
                    print(f"  Warning / Avviso: cannot get Agent {agent_id}: {e}")
            
            if not actions:
                self.send_response(command_id, "failed", error="No valid agents / Nessun agente valido")
                return False
            
            # Execute batch interview / Esegui interview batch
            await self.env.step(actions)
            
            # Collect all results / Raccogli tutti i risultati
            results = {}
            for agent_id in agent_prompts.keys():
                result = self._get_interview_result(agent_id)
                results[agent_id] = result
            
            self.send_response(command_id, "completed", result={
                "interviews_count": len(results),
                "results": results
            })
            print(f"  Batch Interview completed / completata: {len(results)} agents")
            return True
            
        except Exception as e:
            error_msg = str(e)
            print(f"  Batch Interview failed / fallita: {error_msg}")
            self.send_response(command_id, "failed", error=error_msg)
            return False
    
    def _get_interview_result(self, agent_id: int) -> Dict[str, Any]:
        """Fetch latest interview result from DB / Recupera ultimo risultato interview da DB."""
        db_path = os.path.join(self.simulation_dir, "reddit_simulation.db")
        
        result = {
            "agent_id": agent_id,
            "response": None,
            "timestamp": None
        }
        
        if not os.path.exists(db_path):
            return result
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Query latest interview record / Cerca ultimo record interview
            cursor.execute("""
                SELECT user_id, info, created_at
                FROM trace
                WHERE action = ? AND user_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (ActionType.INTERVIEW.value, agent_id))
            
            row = cursor.fetchone()
            if row:
                user_id, info_json, created_at = row
                try:
                    info = json.loads(info_json) if info_json else {}
                    result["response"] = info.get("response", info)
                    result["timestamp"] = created_at
                except json.JSONDecodeError:
                    result["response"] = info_json
            
            conn.close()
            
        except Exception as e:
            print(f"  Failed to read Interview result / Lettura risultato Interview fallita: {e}")
        
        return result
    
    async def process_commands(self) -> bool:
        """
        Process all pending commands / Elabora tutti i comandi in attesa.
        
        Returns:
            True to keep running, False to exit / True continua, False esci
        """
        command = self.poll_command()
        if not command:
            return True
        
        command_id = command.get("command_id")
        command_type = command.get("command_type")
        args = command.get("args", {})
        
        print(f"\nReceived IPC command / Comando IPC ricevuto: {command_type}, id={command_id}")
        
        if command_type == CommandType.INTERVIEW:
            await self.handle_interview(
                command_id,
                args.get("agent_id", 0),
                args.get("prompt", "")
            )
            return True
            
        elif command_type == CommandType.BATCH_INTERVIEW:
            await self.handle_batch_interview(
                command_id,
                args.get("interviews", [])
            )
            return True
            
        elif command_type == CommandType.CLOSE_ENV:
            print("Received close-environment command / Ricevuto comando chiusura ambiente")
            self.send_response(command_id, "completed", result={"message": "Environment will close soon / L'ambiente verra chiuso a breve"})
            return False
        
        else:
            self.send_response(command_id, "failed", error=f"Unknown command type / Tipo comando sconosciuto: {command_type}")
            return True


class RedditSimulationRunner:
    """Reddit simulation runner / Esecutore simulazione Reddit."""
    
    # Available Reddit actions (INTERVIEW is manual-only) / Azioni Reddit disponibili (INTERVIEW solo manuale)
    AVAILABLE_ACTIONS = [
        ActionType.LIKE_POST,
        ActionType.DISLIKE_POST,
        ActionType.CREATE_POST,
        ActionType.CREATE_COMMENT,
        ActionType.LIKE_COMMENT,
        ActionType.DISLIKE_COMMENT,
        ActionType.SEARCH_POSTS,
        ActionType.SEARCH_USER,
        ActionType.TREND,
        ActionType.REFRESH,
        ActionType.DO_NOTHING,
        ActionType.FOLLOW,
        ActionType.MUTE,
    ]
    
    def __init__(self, config_path: str, wait_for_commands: bool = True):
        """
        Initialize simulation runner / Inizializza esecutore simulazione.
        
        Args:
            config_path: config file path (simulation_config.json) / percorso file config (simulation_config.json)
            wait_for_commands: wait commands after simulation (default True) / attendi comandi dopo simulazione (default True)
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.simulation_dir = os.path.dirname(config_path)
        self.wait_for_commands = wait_for_commands
        self.env = None
        self.agent_graph = None
        self.ipc_handler = None
        
    def _load_config(self) -> Dict[str, Any]:
        """Load config file / Carica file configurazione."""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _get_profile_path(self) -> str:
        """Get profile file path / Ottieni percorso file profilo."""
        return os.path.join(self.simulation_dir, "reddit_profiles.json")
    
    def _get_db_path(self) -> str:
        """Get database path / Ottieni percorso database."""
        return os.path.join(self.simulation_dir, "reddit_simulation.db")
    
    def _create_model(self):
        """
        Create LLM model / Crea modello LLM.

        Uses project-root .env configuration with highest priority /
        Usa la configurazione .env nella root progetto con priorita massima:
        - LLM_API_KEY: API key / chiave API
        - LLM_BASE_URL: API base URL / URL base API
        - LLM_MODEL_NAME: model name / nome modello
        """
        # Prefer .env values / Preferisce valori da .env
        llm_api_key = os.environ.get("LLM_API_KEY", "")
        llm_base_url = os.environ.get("LLM_BASE_URL", "")
        llm_model = os.environ.get("LLM_MODEL_NAME", "")
        
        # Fallback to config when .env missing / Fallback a config se .env manca
        if not llm_model:
            llm_model = self.config.get("llm_model", "gpt-4o-mini")
        
        # Set camel-ai environment vars / Imposta variabili ambiente camel-ai
        if llm_api_key:
            os.environ["OPENAI_API_KEY"] = llm_api_key
        
        if not os.environ.get("OPENAI_API_KEY"):
            raise ValueError("Missing API Key: set LLM_API_KEY in project-root .env / Chiave API mancante: imposta LLM_API_KEY nel file .env in root progetto")
        
        if llm_base_url:
            os.environ["OPENAI_API_BASE_URL"] = llm_base_url
        
        print(f"LLM config / configurazione: model={llm_model}, base_url={llm_base_url[:40] if llm_base_url else 'default / predefinito'}...")
        
        return ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=llm_model,
        )
    
    def _get_active_agents_for_round(
        self, 
        env, 
        current_hour: int,
        round_num: int
    ) -> List:
        """
        Decide active agents for current round using time/config /
        Decide quali agenti attivare nel round corrente in base a tempo/config.
        """
        time_config = self.config.get("time_config", {})
        agent_configs = self.config.get("agent_configs", [])
        
        base_min = time_config.get("agents_per_hour_min", 5)
        base_max = time_config.get("agents_per_hour_max", 20)
        
        peak_hours = time_config.get("peak_hours", [9, 10, 11, 14, 15, 20, 21, 22])
        off_peak_hours = time_config.get("off_peak_hours", [0, 1, 2, 3, 4, 5])
        
        if current_hour in peak_hours:
            multiplier = time_config.get("peak_activity_multiplier", 1.5)
        elif current_hour in off_peak_hours:
            multiplier = time_config.get("off_peak_activity_multiplier", 0.3)
        else:
            multiplier = 1.0
        
        target_count = int(random.uniform(base_min, base_max) * multiplier)
        
        candidates = []
        for cfg in agent_configs:
            agent_id = cfg.get("agent_id", 0)
            active_hours = cfg.get("active_hours", list(range(8, 23)))
            activity_level = cfg.get("activity_level", 0.5)
            
            if current_hour not in active_hours:
                continue
            
            if random.random() < activity_level:
                candidates.append(agent_id)
        
        selected_ids = random.sample(
            candidates, 
            min(target_count, len(candidates))
        ) if candidates else []
        
        active_agents = []
        for agent_id in selected_ids:
            try:
                agent = env.agent_graph.get_agent(agent_id)
                active_agents.append((agent_id, agent))
            except Exception:
                pass
        
        return active_agents
    
    async def run(self, max_rounds: int = None):
        """Run Reddit simulation / Esegui simulazione Reddit
        
        Args:
            max_rounds: maximum simulation rounds (optional, truncates long runs) / massimo numero di round (opzionale, tronca simulazioni lunghe)
        """
        print("=" * 60)
        print("OASIS Reddit simulation / simulazione OASIS Reddit")
        print(f"config file / file di configurazione: {self.config_path}")
        print(f"simulation ID / ID simulazione: {self.config.get('simulation_id', 'unknown')}")
        print(f"wait-for-commands mode / modalita attesa comandi: {'enabled / abilitato' if self.wait_for_commands else 'disabled / disabilitato'}")
        print("=" * 60)
        
        time_config = self.config.get("time_config", {})
        total_hours = time_config.get("total_simulation_hours", 72)
        minutes_per_round = time_config.get("minutes_per_round", 30)
        total_rounds = (total_hours * 60) // minutes_per_round
        
        # if max rounds is specified, truncate / se e specificato un massimo, tronca
        if max_rounds is not None and max_rounds > 0:
            original_rounds = total_rounds
            total_rounds = min(total_rounds, max_rounds)
            if total_rounds < original_rounds:
                print(f"\nrounds truncated / round troncati: {original_rounds} -> {total_rounds} (max_rounds={max_rounds})")
        
        print(f"\nsimulation parameters / parametri simulazione:")
        print(f"  - total simulation duration / durata totale simulazione: {total_hours}h")
        print(f"  - time per round / tempo per round: {minutes_per_round}min")
        print(f"  - total rounds / round totali: {total_rounds}")
        if max_rounds:
            print(f"  - max rounds limit / limite massimo round: {max_rounds}")
        print(f"  - Agent count / numero agenti: {len(self.config.get('agent_configs', []))}")
        
        print("\ninitialize LLM model / inizializza modello LLM...")
        model = self._create_model()
        
        print("load Agent profile / carica profilo Agent...")
        profile_path = self._get_profile_path()
        if not os.path.exists(profile_path):
            print(f"error: profile file does not exist / errore: il file profile non esiste: {profile_path}")
            return
        
        self.agent_graph = await generate_reddit_agent_graph(
            profile_path=profile_path,
            model=model,
            available_actions=self.AVAILABLE_ACTIONS,
        )
        
        db_path = self._get_db_path()
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"deleted old database / eliminato vecchio database: {db_path}")
        
        print("create OASIS environment / crea ambiente OASIS...")
        self.env = oasis.make(
            agent_graph=self.agent_graph,
            platform=oasis.DefaultPlatformType.REDDIT,
            database_path=db_path,
            semaphore=30,  # limit max concurrent LLM requests to avoid API overload / limita richieste LLM concorrenti per evitare sovraccarico API
        )
        
        await self.env.reset()
        print("environment initialization completed / inizializzazione ambiente completata\n")
        
        # initialize IPC handler / inizializza gestore IPC
        self.ipc_handler = IPCHandler(self.simulation_dir, self.env, self.agent_graph)
        self.ipc_handler.update_status("running")
        
        # execute initial events / esegui eventi iniziali
        event_config = self.config.get("event_config", {})
        initial_posts = event_config.get("initial_posts", [])
        
        if initial_posts:
            print(f"execute initial events ({len(initial_posts)} initial posts / post iniziali)...")
            initial_actions = {}
            for post in initial_posts:
                agent_id = post.get("poster_agent_id", 0)
                content = post.get("content", "")
                try:
                    agent = self.env.agent_graph.get_agent(agent_id)
                    if agent in initial_actions:
                        if not isinstance(initial_actions[agent], list):
                            initial_actions[agent] = [initial_actions[agent]]
                        initial_actions[agent].append(ManualAction(
                            action_type=ActionType.CREATE_POST,
                            action_args={"content": content}
                        ))
                    else:
                        initial_actions[agent] = ManualAction(
                            action_type=ActionType.CREATE_POST,
                            action_args={"content": content}
                        )
                except Exception as e:
                    print(f"  warning: failed to create initial post for Agent / avviso: impossibile creare post iniziale per Agent {agent_id}: {e}")
            
            if initial_actions:
                await self.env.step(initial_actions)
                print(f"  published / pubblicati {len(initial_actions)} initial posts / post iniziali")
        
        # main simulation loop / ciclo principale simulazione
        print("\nstart simulation loop / avvio ciclo simulazione...")
        start_time = datetime.now()
        
        for round_num in range(total_rounds):
            simulated_minutes = round_num * minutes_per_round
            simulated_hour = (simulated_minutes // 60) % 24
            simulated_day = simulated_minutes // (60 * 24) + 1
            
            active_agents = self._get_active_agents_for_round(
                self.env, simulated_hour, round_num
            )
            
            if not active_agents:
                continue
            
            actions = {
                agent: LLMAction()
                for _, agent in active_agents
            }
            
            await self.env.step(actions)
            
            if (round_num + 1) % 10 == 0 or round_num == 0:
                elapsed = (datetime.now() - start_time).total_seconds()
                progress = (round_num + 1) / total_rounds * 100
                print(f"  [Day {simulated_day}, {simulated_hour:02d}:00] "
                      f"Round {round_num + 1}/{total_rounds} ({progress:.1f}%) "
                      f"- {len(active_agents)} agents active "
                      f"- elapsed: {elapsed:.1f}s")
        
        total_elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\nsimulation loop completed / ciclo simulazione completato!")
        print(f"  - total elapsed / tempo totale: {total_elapsed:.1f}s")
        print(f"  - database / database: {db_path}")
        
        # whether to enter wait-for-commands mode / se entrare in modalita attesa comandi
        if self.wait_for_commands:
            print("\n" + "=" * 60)
            print("entering wait-for-commands mode - environment stays alive / entro in modalita attesa comandi - ambiente attivo")
            print("supported commands / comandi supportati: interview, batch_interview, close_env")
            print("=" * 60)
            
            self.ipc_handler.update_status("alive")
            
            # wait-for-commands loop (uses global _shutdown_event) / ciclo attesa comandi (usa _shutdown_event globale)
            try:
                while not _shutdown_event.is_set():
                    should_continue = await self.ipc_handler.process_commands()
                    if not should_continue:
                        break
                    try:
                        await asyncio.wait_for(_shutdown_event.wait(), timeout=0.5)
                        break  # received exit signal / ricevuto segnale di uscita
                    except asyncio.TimeoutError:
                        pass
            except KeyboardInterrupt:
                print("\ninterrupt signal received / ricevuto segnale di interruzione")
            except asyncio.CancelledError:
                print("\ntask cancelled / task annullato")
            except Exception as e:
                print(f"\ncommand handling error / errore gestione comando: {e}")
            
            print("\nclose environment / chiudi ambiente...")
        
        # close environment / chiudi ambiente
        self.ipc_handler.update_status("stopped")
        await self.env.close()
        
        print("environment closed / ambiente chiuso")
        print("=" * 60)


async def main():
    parser = argparse.ArgumentParser(description='OASIS Reddit simulation / simulazione OASIS Reddit')
    parser.add_argument(
        '--config', 
        type=str, 
        required=True,
        help='config file path (simulation_config.json) / percorso file configurazione (simulation_config.json)'
    )
    parser.add_argument(
        '--max-rounds',
        type=int,
        default=None,
        help='maximum simulation rounds (optional, truncates long runs) / massimo round simulazione (opzionale, tronca simulazioni lunghe)'
    )
    parser.add_argument(
        '--no-wait',
        action='store_true',
        default=False,
        help='close environment immediately after simulation, without wait-for-commands mode / chiudi ambiente subito dopo la simulazione, senza modalita attesa comandi'
    )
    
    args = parser.parse_args()
    
    # create shutdown event at start of main / crea evento shutdown all avvio di main
    global _shutdown_event
    _shutdown_event = asyncio.Event()
    
    if not os.path.exists(args.config):
        print(f"error: config file does not exist / errore: file configurazione non esiste: {args.config}")
        sys.exit(1)
    
    # initialize logging config (fixed filename, clean old logs) / inizializza configurazione log (nome fisso, pulisce log vecchi)
    simulation_dir = os.path.dirname(args.config) or "."
    setup_oasis_logging(os.path.join(simulation_dir, "log"))
    
    runner = RedditSimulationRunner(
        config_path=args.config,
        wait_for_commands=not args.no_wait
    )
    await runner.run(max_rounds=args.max_rounds)


def setup_signal_handlers():
    """
    set signal handlers to ensure proper exit on SIGTERM/SIGINT / imposta handler segnali per uscita corretta su SIGTERM/SIGINT
    allow graceful resource cleanup (close database, environment, etc.) / consente pulizia corretta delle risorse (chiusura database, ambiente, ecc.)
    """
    def signal_handler(signum, frame):
        global _cleanup_done
        sig_name = "SIGTERM" if signum == signal.SIGTERM else "SIGINT"
        print(f"\nreceived signal, shutting down / ricevuto segnale, chiusura in corso...")
        if not _cleanup_done:
            _cleanup_done = True
            if _shutdown_event:
                _shutdown_event.set()
        else:
            # force exit only after receiving a duplicate signal / uscita forzata solo dopo un segnale duplicato
            print("force exit / uscita forzata...")
            sys.exit(1)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":
    setup_signal_handlers()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nprogram interrupted / programma interrotto")
    except SystemExit:
        pass
    finally:
        print("simulation process exited / processo simulazione terminato")

