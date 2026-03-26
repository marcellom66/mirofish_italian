"""
OASIS dual-platform parallel simulation preset script /
script preset per simulazione parallela OASIS a doppia piattaforma.
Runs Twitter and Reddit simulations together using the same config file /
esegue insieme simulazioni Twitter e Reddit usando lo stesso file di configurazione.

Features / Funzionalita:
- Dual-platform (Twitter + Reddit) parallel simulation /
    simulazione parallela a doppia piattaforma (Twitter + Reddit)
- Keep environments alive after simulation, entering wait-for-commands mode /
    mantiene gli ambienti attivi dopo la simulazione, entrando in modalita attesa comandi
- Supports Interview commands via IPC /
    supporta comandi Interview via IPC
- Supports single-Agent and batch interviews /
    supporta interviste singolo Agent e batch
- Supports remote environment shutdown command /
    supporta comando remoto di chiusura ambiente

Usage / Utilizzo:
        python run_parallel_simulation.py --config simulation_config.json
        python run_parallel_simulation.py --config simulation_config.json --no-wait  # close immediately / chiudi subito
        python run_parallel_simulation.py --config simulation_config.json --twitter-only
        python run_parallel_simulation.py --config simulation_config.json --reddit-only

Log layout / Struttura log:
        sim_xxx/
        ├── twitter/
        │   └── actions.jsonl    # Twitter platform action logs / log azioni piattaforma Twitter
        ├── reddit/
        │   └── actions.jsonl    # Reddit platform action logs / log azioni piattaforma Reddit
        ├── simulation.log       # main simulation process log / log processo simulazione principale
        └── run_state.json       # runtime state (for API queries) / stato runtime (per query API)
"""

# ============================================================
# Fix Windows encoding issues: set UTF-8 before all imports /
# Corregge problemi di codifica su Windows: imposta UTF-8 prima di tutti gli import.
# This addresses third-party OASIS file reads without explicit encoding /
# Questo risolve letture file OASIS senza codifica esplicita.
# ============================================================
import sys
import os

if sys.platform == 'win32':
    # Set Python default I/O encoding to UTF-8 /
    # Imposta la codifica I/O di default di Python a UTF-8.
    os.environ.setdefault('PYTHONUTF8', '1')
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    
    # Reconfigure stdout/stderr to UTF-8 (avoid console mojibake) /
    # Riconfigura stdout/stderr in UTF-8 (evita testo illeggibile in console).
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    
    # Force default encoding affecting open() default behavior /
    # Forza la codifica di default che influenza open().
    # Runtime setting may not always apply from process start, so patch built-in open /
    # L'impostazione runtime potrebbe non bastare all'avvio, quindi patchiamo open built-in.
    import builtins
    _original_open = builtins.open
    
    def _utf8_open(file, mode='r', buffering=-1, encoding=None, errors=None, 
                   newline=None, closefd=True, opener=None):
        """
        Wrap open() and default to UTF-8 in text mode /
        Wrapper di open() con default UTF-8 in modalita testo.
        Helps with third-party libraries (like OASIS) that omit encoding /
        Aiuta con librerie terze (come OASIS) che omettono la codifica.
        """
        # Only for text mode (non-binary) with unspecified encoding /
        # Solo in modalita testo (non binaria) e codifica non specificata.
        if encoding is None and 'b' not in mode:
            encoding = 'utf-8'
        return _original_open(file, mode, buffering, encoding, errors, 
                              newline, closefd, opener)
    
    builtins.open = _utf8_open

import argparse
import asyncio
import json
import logging
import multiprocessing
import random
import signal
import sqlite3
import warnings
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple


# Global variables for signal handling / Variabili globali per gestione segnali
_shutdown_event = None
_cleanup_done = False

# Add backend paths to sys.path / Aggiungi percorsi backend a sys.path
# Script is expected under backend/scripts/ / Lo script e previsto in backend/scripts/
_scripts_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.abspath(os.path.join(_scripts_dir, '..'))
_project_root = os.path.abspath(os.path.join(_backend_dir, '..'))
sys.path.insert(0, _scripts_dir)
sys.path.insert(0, _backend_dir)

# Load project-root .env (contains LLM_API_KEY and related settings) /
# Carica il .env alla root progetto (contiene LLM_API_KEY e impostazioni correlate)
from dotenv import load_dotenv
_env_file = os.path.join(_project_root, '.env')
if os.path.exists(_env_file):
    load_dotenv(_env_file)
    print(f"loaded env config / configurazione ambiente caricata: {_env_file}")
else:
    # Try loading backend/.env / Prova a caricare backend/.env
    _backend_env = os.path.join(_backend_dir, '.env')
    if os.path.exists(_backend_env):
        load_dotenv(_backend_env)
        print(f"loaded env config / configurazione ambiente caricata: {_backend_env}")


class MaxTokensWarningFilter(logging.Filter):
    """Filter camel-ai max_tokens warnings (intentional: model decides token budget) /
    Filtra warning camel-ai su max_tokens (intenzionale: decide il modello)."""
    
    def filter(self, record):
        # Filter max_tokens warning records / Filtra record warning max_tokens
        if "max_tokens" in record.getMessage() and "Invalid or missing" in record.getMessage():
            return False
        return True


# Add filter at module load so it applies before camel code runs /
# Aggiunge il filtro al load del modulo prima dell'esecuzione codice camel
logging.getLogger().addFilter(MaxTokensWarningFilter())


def disable_oasis_logging():
    """
    Disable verbose OASIS logs / Disabilita log verbosi OASIS.
    OASIS logs are very noisy; we rely on our own action_logger /
    I log OASIS sono molto rumorosi; usiamo il nostro action_logger.
    """
    # Disable OASIS loggers / Disabilita logger OASIS
    oasis_loggers = [
        "social.agent",
        "social.twitter",
        "social.rec",
        "oasis.env",
        "table",
    ]

    for logger_name in oasis_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.CRITICAL)  # critical only / solo errori critici
        logger.handlers.clear()
        logger.propagate = False


def init_logging_for_simulation(simulation_dir: str):
    """
    Initialize simulation logging / Inizializza logging simulazione.
    
    Args:
        simulation_dir: simulation directory path / percorso directory simulazione
    """
    # Disable verbose OASIS logs / Disabilita log OASIS verbosi
    disable_oasis_logging()
    
    # Clean old log directory if present / Pulisci directory log precedente se presente
    old_log_dir = os.path.join(simulation_dir, "log")
    if os.path.exists(old_log_dir):
        import shutil
        shutil.rmtree(old_log_dir, ignore_errors=True)


from action_logger import SimulationLogManager, PlatformActionLogger

try:
    from camel.models import ModelFactory
    from camel.types import ModelPlatformType
    import oasis
    from oasis import (
        ActionType,
        LLMAction,
        ManualAction,
        generate_twitter_agent_graph,
        generate_reddit_agent_graph
    )
except ImportError as e:
    print(f"error: missing dependency / errore: dipendenza mancante {e}")
    print("please install first / installa prima: pip install oasis-ai camel-ai")
    sys.exit(1)


# Twitter available actions (INTERVIEW excluded; manual only) /
# Azioni Twitter disponibili (INTERVIEW esclusa; solo manuale)
TWITTER_ACTIONS = [
    ActionType.CREATE_POST,
    ActionType.LIKE_POST,
    ActionType.REPOST,
    ActionType.FOLLOW,
    ActionType.DO_NOTHING,
    ActionType.QUOTE_POST,
]

# Reddit available actions (INTERVIEW excluded; manual only) /
# Azioni Reddit disponibili (INTERVIEW esclusa; solo manuale)
REDDIT_ACTIONS = [
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


# IPC constants / Costanti IPC
IPC_COMMANDS_DIR = "ipc_commands"
IPC_RESPONSES_DIR = "ipc_responses"
ENV_STATUS_FILE = "env_status.json"

class CommandType:
    """Command type constants / Costanti tipo comando."""
    INTERVIEW = "interview"
    BATCH_INTERVIEW = "batch_interview"
    CLOSE_ENV = "close_env"


class ParallelIPCHandler:
    """
    Dual-platform IPC command handler /
    Gestore comandi IPC a doppia piattaforma.

    Manages both platform environments and processes Interview commands /
    Gestisce entrambi gli ambienti piattaforma ed elabora comandi Interview.
    """
    
    def __init__(
        self,
        simulation_dir: str,
        twitter_env=None,
        twitter_agent_graph=None,
        reddit_env=None,
        reddit_agent_graph=None
    ):
        self.simulation_dir = simulation_dir
        self.twitter_env = twitter_env
        self.twitter_agent_graph = twitter_agent_graph
        self.reddit_env = reddit_env
        self.reddit_agent_graph = reddit_agent_graph
        
        self.commands_dir = os.path.join(simulation_dir, IPC_COMMANDS_DIR)
        self.responses_dir = os.path.join(simulation_dir, IPC_RESPONSES_DIR)
        self.status_file = os.path.join(simulation_dir, ENV_STATUS_FILE)
        
        # Ensure directories exist / Assicura che le directory esistano
        os.makedirs(self.commands_dir, exist_ok=True)
        os.makedirs(self.responses_dir, exist_ok=True)
    
    def update_status(self, status: str):
        """Update environment status / Aggiorna stato ambiente."""
        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump({
                "status": status,
                "twitter_available": self.twitter_env is not None,
                "reddit_available": self.reddit_env is not None,
                "timestamp": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
    
    def poll_command(self) -> Optional[Dict[str, Any]]:
        """Poll pending command / Legge comando pendente."""
        if not os.path.exists(self.commands_dir):
            return None
        
        # Read command files sorted by time / Legge file comandi ordinati per tempo
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
        
        # Remove command file / Rimuovi file comando
        command_file = os.path.join(self.commands_dir, f"{command_id}.json")
        try:
            os.remove(command_file)
        except OSError:
            pass
    
    def _get_env_and_graph(self, platform: str):
        """
        Get env and agent_graph for target platform /
        Ottieni env e agent_graph per la piattaforma richiesta.

        Args:
            platform: platform name ("twitter" or "reddit") /
                nome piattaforma ("twitter" o "reddit")

        Returns:
            (env, agent_graph, platform_name) or (None, None, None) /
            (env, agent_graph, platform_name) oppure (None, None, None)
        """
        if platform == "twitter" and self.twitter_env:
            return self.twitter_env, self.twitter_agent_graph, "twitter"
        elif platform == "reddit" and self.reddit_env:
            return self.reddit_env, self.reddit_agent_graph, "reddit"
        else:
            return None, None, None
    
    async def _interview_single_platform(self, agent_id: int, prompt: str, platform: str) -> Dict[str, Any]:
        """
        Execute Interview on a single platform /
        Esegui Interview su una singola piattaforma.

        Returns:
            Dict with result, or dict with error /
            Dizionario con risultato, oppure dizionario con errore
        """
        env, agent_graph, actual_platform = self._get_env_and_graph(platform)
        
        if not env or not agent_graph:
            return {"platform": platform, "error": f"{platform} platform unavailable / piattaforma {platform} non disponibile"}
        
        try:
            agent = agent_graph.get_agent(agent_id)
            interview_action = ManualAction(
                action_type=ActionType.INTERVIEW,
                action_args={"prompt": prompt}
            )
            actions = {agent: interview_action}
            await env.step(actions)
            
            result = self._get_interview_result(agent_id, actual_platform)
            result["platform"] = actual_platform
            return result
            
        except Exception as e:
            return {"platform": platform, "error": str(e)}
    
    async def handle_interview(self, command_id: str, agent_id: int, prompt: str, platform: str = None) -> bool:
        """
        Handle single-Agent interview command /
        Gestisce comando interview per singolo Agent.

        Args:
            command_id: command ID / ID comando
            agent_id: Agent ID
            prompt: interview question / domanda intervista
            platform: optional target platform / piattaforma target opzionale
                - "twitter": interview Twitter only / intervista solo Twitter
                - "reddit": interview Reddit only / intervista solo Reddit
                - None: interview both and return merged results /
                  None: intervista entrambe e restituisce risultato aggregato

        Returns:
            True on success, False on failure / True se successo, False se fallimento
        """
        # If platform is specified, interview only that platform /
        # Se la piattaforma e specificata, intervista solo quella
        if platform in ("twitter", "reddit"):
            result = await self._interview_single_platform(agent_id, prompt, platform)
            
            if "error" in result:
                self.send_response(command_id, "failed", error=result["error"])
                print(f"  Interview failed / fallita: agent_id={agent_id}, platform={platform}, error={result['error']}")
                return False
            else:
                self.send_response(command_id, "completed", result=result)
                print(f"  Interview completed / completata: agent_id={agent_id}, platform={platform}")
                return True
        
        # No platform specified: interview both /
        # Nessuna piattaforma specificata: intervista entrambe
        if not self.twitter_env and not self.reddit_env:
            self.send_response(command_id, "failed", error="no simulation environments available / nessun ambiente di simulazione disponibile")
            return False
        
        results = {
            "agent_id": agent_id,
            "prompt": prompt,
            "platforms": {}
        }
        success_count = 0
        
        # Interview both platforms in parallel / Intervista entrambe in parallelo
        tasks = []
        platforms_to_interview = []
        
        if self.twitter_env:
            tasks.append(self._interview_single_platform(agent_id, prompt, "twitter"))
            platforms_to_interview.append("twitter")
        
        if self.reddit_env:
            tasks.append(self._interview_single_platform(agent_id, prompt, "reddit"))
            platforms_to_interview.append("reddit")
        
        # Execute in parallel / Esegui in parallelo
        platform_results = await asyncio.gather(*tasks)
        
        for platform_name, platform_result in zip(platforms_to_interview, platform_results):
            results["platforms"][platform_name] = platform_result
            if "error" not in platform_result:
                success_count += 1
        
        if success_count > 0:
            self.send_response(command_id, "completed", result=results)
            print(f"  Interview completed / completata: agent_id={agent_id}, successful platforms / piattaforme riuscite={success_count}/{len(platforms_to_interview)}")
            return True
        else:
            errors = [f"{p}: {r.get('error', 'unknown error / errore sconosciuto')}" for p, r in results["platforms"].items()]
            self.send_response(command_id, "failed", error="; ".join(errors))
            print(f"  Interview failed / fallita: agent_id={agent_id}, all platforms failed / tutte le piattaforme fallite")
            return False
    
    async def handle_batch_interview(self, command_id: str, interviews: List[Dict], platform: str = None) -> bool:
        """
        Handle batch interview command /
        Gestisce comando interview in batch.

        Args:
            command_id: command ID / ID comando
            interviews: [{"agent_id": int, "prompt": str, "platform": str(optional)}, ...]
            platform: default platform (overridable per item) /
                piattaforma di default (sovrascrivibile per item)
                - "twitter": interview Twitter only / intervista solo Twitter
                - "reddit": interview Reddit only / intervista solo Reddit
                - None: each Agent is interviewed on both platforms /
                  None: ogni Agent viene intervistato su entrambe le piattaforme
        """
        # Group by platform / Raggruppa per piattaforma
        twitter_interviews = []
        reddit_interviews = []
        both_platforms_interviews = []  # interview both platforms / intervista su entrambe
        
        for interview in interviews:
            item_platform = interview.get("platform", platform)
            if item_platform == "twitter":
                twitter_interviews.append(interview)
            elif item_platform == "reddit":
                reddit_interviews.append(interview)
            else:
                # No platform specified: interview both / Nessuna piattaforma: intervista entrambe
                both_platforms_interviews.append(interview)
        
        # Split dual-platform requests into both queues / Distribuisci richieste dual-platform su entrambe le code
        if both_platforms_interviews:
            if self.twitter_env:
                twitter_interviews.extend(both_platforms_interviews)
            if self.reddit_env:
                reddit_interviews.extend(both_platforms_interviews)
        
        results = {}
        
        # Process Twitter interviews / Elabora interviste Twitter
        if twitter_interviews and self.twitter_env:
            try:
                twitter_actions = {}
                for interview in twitter_interviews:
                    agent_id = interview.get("agent_id")
                    prompt = interview.get("prompt", "")
                    try:
                        agent = self.twitter_agent_graph.get_agent(agent_id)
                        twitter_actions[agent] = ManualAction(
                            action_type=ActionType.INTERVIEW,
                            action_args={"prompt": prompt}
                        )
                    except Exception as e:
                        print(f"  warning / avviso: cannot get Twitter Agent {agent_id} / impossibile ottenere Twitter Agent {agent_id}: {e}")
                
                if twitter_actions:
                    await self.twitter_env.step(twitter_actions)
                    
                    for interview in twitter_interviews:
                        agent_id = interview.get("agent_id")
                        result = self._get_interview_result(agent_id, "twitter")
                        result["platform"] = "twitter"
                        results[f"twitter_{agent_id}"] = result
            except Exception as e:
                print(f"  Twitter batch Interview failed / batch Interview Twitter fallito: {e}")
        
        # Process Reddit interviews / Elabora interviste Reddit
        if reddit_interviews and self.reddit_env:
            try:
                reddit_actions = {}
                for interview in reddit_interviews:
                    agent_id = interview.get("agent_id")
                    prompt = interview.get("prompt", "")
                    try:
                        agent = self.reddit_agent_graph.get_agent(agent_id)
                        reddit_actions[agent] = ManualAction(
                            action_type=ActionType.INTERVIEW,
                            action_args={"prompt": prompt}
                        )
                    except Exception as e:
                        print(f"  warning / avviso: cannot get Reddit Agent {agent_id} / impossibile ottenere Reddit Agent {agent_id}: {e}")
                
                if reddit_actions:
                    await self.reddit_env.step(reddit_actions)
                    
                    for interview in reddit_interviews:
                        agent_id = interview.get("agent_id")
                        result = self._get_interview_result(agent_id, "reddit")
                        result["platform"] = "reddit"
                        results[f"reddit_{agent_id}"] = result
            except Exception as e:
                print(f"  Reddit batch Interview failed / batch Interview Reddit fallito: {e}")
        
        if results:
            self.send_response(command_id, "completed", result={
                "interviews_count": len(results),
                "results": results
            })
            print(f"  batch Interview completed / batch Interview completata: {len(results)} agents / agenti")
            return True
        else:
            self.send_response(command_id, "failed", error="no successful interviews / nessuna interview riuscita")
            return False
    
    def _get_interview_result(self, agent_id: int, platform: str) -> Dict[str, Any]:
        """Get latest Interview result from DB / Ottieni ultimo risultato Interview dal DB."""
        db_path = os.path.join(self.simulation_dir, f"{platform}_simulation.db")
        
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
            
            # Query latest Interview row / Leggi ultima riga Interview
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
            print(f"  failed to read Interview result / lettura risultato Interview fallita: {e}")
        
        return result
    
    async def process_commands(self) -> bool:
        """
        Process all pending commands /
        Elabora tutti i comandi pendenti.

        Returns:
            True to continue, False to exit / True per continuare, False per uscire
        """
        command = self.poll_command()
        if not command:
            return True
        
        command_id = command.get("command_id")
        command_type = command.get("command_type")
        args = command.get("args", {})
        
        print(f"\nreceived IPC command / comando IPC ricevuto: {command_type}, id={command_id}")
        
        if command_type == CommandType.INTERVIEW:
            await self.handle_interview(
                command_id,
                args.get("agent_id", 0),
                args.get("prompt", ""),
                args.get("platform")
            )
            return True
            
        elif command_type == CommandType.BATCH_INTERVIEW:
            await self.handle_batch_interview(
                command_id,
                args.get("interviews", []),
                args.get("platform")
            )
            return True
            
        elif command_type == CommandType.CLOSE_ENV:
            print("received close-environment command / ricevuto comando chiusura ambiente")
            self.send_response(command_id, "completed", result={"message": "environment will close soon / l'ambiente verra chiuso a breve"})
            return False
        
        else:
            self.send_response(command_id, "failed", error=f"unknown command type / tipo comando sconosciuto: {command_type}")
            return True


def load_config(config_path: str) -> Dict[str, Any]:
    """Load config file / Carica file di configurazione."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


# Non-core actions to filter out (low analysis value) /
# Azioni non core da filtrare (basso valore analitico)
FILTERED_ACTIONS = {'refresh', 'sign_up'}

# Action type mapping (DB name -> canonical name) /
# Mappa tipi azione (nome DB -> nome canonico)
ACTION_TYPE_MAP = {
    'create_post': 'CREATE_POST',
    'like_post': 'LIKE_POST',
    'dislike_post': 'DISLIKE_POST',
    'repost': 'REPOST',
    'quote_post': 'QUOTE_POST',
    'follow': 'FOLLOW',
    'mute': 'MUTE',
    'create_comment': 'CREATE_COMMENT',
    'like_comment': 'LIKE_COMMENT',
    'dislike_comment': 'DISLIKE_COMMENT',
    'search_posts': 'SEARCH_POSTS',
    'search_user': 'SEARCH_USER',
    'trend': 'TREND',
    'do_nothing': 'DO_NOTHING',
    'interview': 'INTERVIEW',
}


def get_agent_names_from_config(config: Dict[str, Any]) -> Dict[int, str]:
    """
    Build mapping agent_id -> entity_name from simulation_config /
    Crea mappatura agent_id -> entity_name da simulation_config.

    This lets actions.jsonl show real entity names instead of aliases like
    "Agent_0" / Consente di mostrare nomi reali invece di alias come "Agent_0".

    Args:
        config: simulation_config.json content / contenuto simulation_config.json

    Returns:
        dict mapping agent_id -> entity_name /
        dizionario mapping agent_id -> entity_name
    """
    agent_names = {}
    agent_configs = config.get("agent_configs", [])
    
    for agent_config in agent_configs:
        agent_id = agent_config.get("agent_id")
        entity_name = agent_config.get("entity_name", f"Agent_{agent_id}")
        if agent_id is not None:
            agent_names[agent_id] = entity_name
    
    return agent_names


def fetch_new_actions_from_db(
    db_path: str,
    last_rowid: int,
    agent_names: Dict[int, str]
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Fetch new action rows from DB and enrich full context /
    Legge nuove azioni dal DB e arricchisce il contesto.

    Args:
        db_path: DB file path / percorso file DB
        last_rowid: max rowid previously read (uses rowid instead of created_at
            because created_at format differs across platforms) /
            max rowid letto in precedenza (usa rowid invece di created_at
            perche il formato created_at varia tra piattaforme)
        agent_names: agent_id -> agent_name mapping /
            mapping agent_id -> agent_name

    Returns:
        (actions_list, new_last_rowid)
        - actions_list: action list with agent_id, agent_name, action_type,
          action_args (with context) / lista azioni con contesto
        - new_last_rowid: new max rowid / nuovo rowid massimo
    """
    actions = []
    new_last_rowid = last_rowid
    
    if not os.path.exists(db_path):
        return actions, new_last_rowid
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Track processed rows by rowid (SQLite built-in incremental field).
        # This avoids created_at format mismatch (Twitter: int, Reddit: datetime string).
        cursor.execute("""
            SELECT rowid, user_id, action, info
            FROM trace
            WHERE rowid > ?
            ORDER BY rowid ASC
        """, (last_rowid,))
        
        for rowid, user_id, action, info_json in cursor.fetchall():
            # Update max rowid / Aggiorna rowid massimo
            new_last_rowid = rowid
            
            # Filter non-core actions / Filtra azioni non core
            if action in FILTERED_ACTIONS:
                continue
            
            # Parse action args / Parsing parametri azione
            try:
                action_args = json.loads(info_json) if info_json else {}
            except json.JSONDecodeError:
                action_args = {}
            
            # Keep only key fields (full values preserved, no truncation).
            simplified_args = {}
            if 'content' in action_args:
                simplified_args['content'] = action_args['content']
            if 'post_id' in action_args:
                simplified_args['post_id'] = action_args['post_id']
            if 'comment_id' in action_args:
                simplified_args['comment_id'] = action_args['comment_id']
            if 'quoted_id' in action_args:
                simplified_args['quoted_id'] = action_args['quoted_id']
            if 'new_post_id' in action_args:
                simplified_args['new_post_id'] = action_args['new_post_id']
            if 'follow_id' in action_args:
                simplified_args['follow_id'] = action_args['follow_id']
            if 'query' in action_args:
                simplified_args['query'] = action_args['query']
            if 'like_id' in action_args:
                simplified_args['like_id'] = action_args['like_id']
            if 'dislike_id' in action_args:
                simplified_args['dislike_id'] = action_args['dislike_id']
            
            # Normalize action type name / Normalizza nome action type
            action_type = ACTION_TYPE_MAP.get(action, action.upper())
            
            # Enrich contextual fields (post text, usernames, etc.).
            _enrich_action_context(cursor, action_type, simplified_args, agent_names)
            
            actions.append({
                'agent_id': user_id,
                'agent_name': agent_names.get(user_id, f'Agent_{user_id}'),
                'action_type': action_type,
                'action_args': simplified_args,
            })
        
        conn.close()
    except Exception as e:
        print(f"failed to read DB actions / lettura azioni DB fallita: {e}")
    
    return actions, new_last_rowid


def _enrich_action_context(
    cursor,
    action_type: str,
    action_args: Dict[str, Any],
    agent_names: Dict[int, str]
) -> None:
    """
    Enrich action with context (post text, usernames, etc.) /
    Arricchisce azione con contesto (testo post, username, ecc.).

    Args:
        cursor: DB cursor / cursore DB
        action_type: action type / tipo azione
        action_args: action args (mutated in-place) /
            parametri azione (modificati in-place)
        agent_names: agent_id -> agent_name mapping /
            mapping agent_id -> agent_name
    """
    try:
        # Like/dislike post: add post content and author.
        if action_type in ('LIKE_POST', 'DISLIKE_POST'):
            post_id = action_args.get('post_id')
            if post_id:
                post_info = _get_post_info(cursor, post_id, agent_names)
                if post_info:
                    action_args['post_content'] = post_info.get('content', '')
                    action_args['post_author_name'] = post_info.get('author_name', '')
        
        # Repost: add original post content and author.
        elif action_type == 'REPOST':
            new_post_id = action_args.get('new_post_id')
            if new_post_id:
                # repost.original_post_id points to the source post
                cursor.execute("""
                    SELECT original_post_id FROM post WHERE post_id = ?
                """, (new_post_id,))
                row = cursor.fetchone()
                if row and row[0]:
                    original_post_id = row[0]
                    original_info = _get_post_info(cursor, original_post_id, agent_names)
                    if original_info:
                        action_args['original_content'] = original_info.get('content', '')
                        action_args['original_author_name'] = original_info.get('author_name', '')
        
        # Quote post: add source content, author and quote content.
        elif action_type == 'QUOTE_POST':
            quoted_id = action_args.get('quoted_id')
            new_post_id = action_args.get('new_post_id')
            
            if quoted_id:
                original_info = _get_post_info(cursor, quoted_id, agent_names)
                if original_info:
                    action_args['original_content'] = original_info.get('content', '')
                    action_args['original_author_name'] = original_info.get('author_name', '')
            
            # Read quote content from created quote post.
            if new_post_id:
                cursor.execute("""
                    SELECT quote_content FROM post WHERE post_id = ?
                """, (new_post_id,))
                row = cursor.fetchone()
                if row and row[0]:
                    action_args['quote_content'] = row[0]
        
        # Follow user: add followed user name.
        elif action_type == 'FOLLOW':
            follow_id = action_args.get('follow_id')
            if follow_id:
                # Resolve followee_id from follow table.
                cursor.execute("""
                    SELECT followee_id FROM follow WHERE follow_id = ?
                """, (follow_id,))
                row = cursor.fetchone()
                if row:
                    followee_id = row[0]
                    target_name = _get_user_name(cursor, followee_id, agent_names)
                    if target_name:
                        action_args['target_user_name'] = target_name
        
        # Mute user: add muted target name.
        elif action_type == 'MUTE':
            # read target from user_id or target_id
            target_id = action_args.get('user_id') or action_args.get('target_id')
            if target_id:
                target_name = _get_user_name(cursor, target_id, agent_names)
                if target_name:
                    action_args['target_user_name'] = target_name
        
        # Like/dislike comment: add comment content and author.
        elif action_type in ('LIKE_COMMENT', 'DISLIKE_COMMENT'):
            comment_id = action_args.get('comment_id')
            if comment_id:
                comment_info = _get_comment_info(cursor, comment_id, agent_names)
                if comment_info:
                    action_args['comment_content'] = comment_info.get('content', '')
                    action_args['comment_author_name'] = comment_info.get('author_name', '')
        
        # Create comment: add referenced post details.
        elif action_type == 'CREATE_COMMENT':
            post_id = action_args.get('post_id')
            if post_id:
                post_info = _get_post_info(cursor, post_id, agent_names)
                if post_info:
                    action_args['post_content'] = post_info.get('content', '')
                    action_args['post_author_name'] = post_info.get('author_name', '')
    
    except Exception as e:
        # Context enrichment failures must not break the main flow.
        print(f"failed to enrich action context / arricchimento contesto azione fallito: {e}")


def _get_post_info(
    cursor,
    post_id: int,
    agent_names: Dict[int, str]
) -> Optional[Dict[str, str]]:
    """
    Get post info / Ottieni info post.

    Args:
        cursor: DB cursor / cursore DB
        post_id: post ID / ID post
        agent_names: agent_id -> agent_name mapping /
            mapping agent_id -> agent_name

    Returns:
        dict with content and author_name, or None /
        dizionario con content e author_name, oppure None
    """
    try:
        cursor.execute("""
            SELECT p.content, p.user_id, u.agent_id
            FROM post p
            LEFT JOIN user u ON p.user_id = u.user_id
            WHERE p.post_id = ?
        """, (post_id,))
        row = cursor.fetchone()
        if row:
            content = row[0] or ''
            user_id = row[1]
            agent_id = row[2]
            
            # Prefer configured names from agent_names.
            author_name = ''
            if agent_id is not None and agent_id in agent_names:
                author_name = agent_names[agent_id]
            elif user_id:
                # Fallback to user table name fields.
                cursor.execute("SELECT name, user_name FROM user WHERE user_id = ?", (user_id,))
                user_row = cursor.fetchone()
                if user_row:
                    author_name = user_row[0] or user_row[1] or ''
            
            return {'content': content, 'author_name': author_name}
    except Exception:
        pass
    return None


def _get_user_name(
    cursor,
    user_id: int,
    agent_names: Dict[int, str]
) -> Optional[str]:
    """
    Get user name / Ottieni nome utente.

    Args:
        cursor: DB cursor / cursore DB
        user_id: user ID / ID utente
        agent_names: agent_id -> agent_name mapping /
            mapping agent_id -> agent_name

    Returns:
        user name, or None / nome utente, oppure None
    """
    try:
        cursor.execute("""
            SELECT agent_id, name, user_name FROM user WHERE user_id = ?
        """, (user_id,))
        row = cursor.fetchone()
        if row:
            agent_id = row[0]
            name = row[1]
            user_name = row[2]
            
            # Prefer configured names from agent_names.
            if agent_id is not None and agent_id in agent_names:
                return agent_names[agent_id]
            return name or user_name or ''
    except Exception:
        pass
    return None


def _get_comment_info(
    cursor,
    comment_id: int,
    agent_names: Dict[int, str]
) -> Optional[Dict[str, str]]:
    """
    Get comment info / Ottieni info commento.

    Args:
        cursor: DB cursor / cursore DB
        comment_id: comment ID / ID commento
        agent_names: agent_id -> agent_name mapping /
            mapping agent_id -> agent_name

    Returns:
        dict with content and author_name, or None /
        dizionario con content e author_name, oppure None
    """
    try:
        cursor.execute("""
            SELECT c.content, c.user_id, u.agent_id
            FROM comment c
            LEFT JOIN user u ON c.user_id = u.user_id
            WHERE c.comment_id = ?
        """, (comment_id,))
        row = cursor.fetchone()
        if row:
            content = row[0] or ''
            user_id = row[1]
            agent_id = row[2]
            
            # Prefer configured names from agent_names.
            author_name = ''
            if agent_id is not None and agent_id in agent_names:
                author_name = agent_names[agent_id]
            elif user_id:
                # Fallback to user table name fields.
                cursor.execute("SELECT name, user_name FROM user WHERE user_id = ?", (user_id,))
                user_row = cursor.fetchone()
                if user_row:
                    author_name = user_row[0] or user_row[1] or ''
            
            return {'content': content, 'author_name': author_name}
    except Exception:
        pass
    return None


def create_model(config: Dict[str, Any], use_boost: bool = False):
    """
    Create LLM model / Crea modello LLM.

    Supports dual LLM settings for parallel simulation speed-up:
    - Generic config: LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_NAME
    - Boost config (optional): LLM_BOOST_API_KEY, LLM_BOOST_BASE_URL,
      LLM_BOOST_MODEL_NAME

    When boost LLM is configured, different platforms can use different API
    providers to improve concurrency /
    Se la config boost e presente, piattaforme diverse possono usare provider
    API diversi per migliorare la concorrenza.

    Args:
        config: simulation config dict / dizionario configurazione simulazione
        use_boost: whether to use boost LLM config if available /
            se usare config LLM boost se disponibile
    """
    # Check boost configuration availability.
    boost_api_key = os.environ.get("LLM_BOOST_API_KEY", "")
    boost_base_url = os.environ.get("LLM_BOOST_BASE_URL", "")
    boost_model = os.environ.get("LLM_BOOST_MODEL_NAME", "")
    has_boost_config = bool(boost_api_key)
    
    # Select LLM config according to settings.
    if use_boost and has_boost_config:
        # Use boost config / Usa config boost
        llm_api_key = boost_api_key
        llm_base_url = boost_base_url
        llm_model = boost_model or os.environ.get("LLM_MODEL_NAME", "")
        config_label = "[Boost LLM / LLM Boost]"
    else:
        # Use generic config / Usa config generica
        llm_api_key = os.environ.get("LLM_API_KEY", "")
        llm_base_url = os.environ.get("LLM_BASE_URL", "")
        llm_model = os.environ.get("LLM_MODEL_NAME", "")
        config_label = "[Generic LLM / LLM Generico]"
    
    # Fallback to config model if not set in .env.
    if not llm_model:
        llm_model = config.get("llm_model", "gpt-4o-mini")
    
    # Export required env vars for camel-ai.
    if llm_api_key:
        os.environ["OPENAI_API_KEY"] = llm_api_key
    
    if not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("missing API key config / configurazione API key mancante: set LLM_API_KEY in project root .env")
    
    if llm_base_url:
        os.environ["OPENAI_API_BASE_URL"] = llm_base_url
    
    print(f"{config_label} model={llm_model}, base_url={llm_base_url[:40] if llm_base_url else 'default / predefinito'}...")
    
    return ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=llm_model,
    )


def get_active_agents_for_round(
    env,
    config: Dict[str, Any],
    current_hour: int,
    round_num: int
) -> List:
    """Select active Agents for current round / Seleziona Agent attivi nel round corrente."""
    time_config = config.get("time_config", {})
    agent_configs = config.get("agent_configs", [])
    
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


class PlatformSimulation:
    """Platform simulation result container / Contenitore risultati simulazione piattaforma."""
    def __init__(self):
        self.env = None
        self.agent_graph = None
        self.total_actions = 0


async def run_twitter_simulation(
    config: Dict[str, Any], 
    simulation_dir: str,
    action_logger: Optional[PlatformActionLogger] = None,
    main_logger: Optional[SimulationLogManager] = None,
    max_rounds: Optional[int] = None
) -> PlatformSimulation:
    """Run Twitter simulation / Esegui simulazione Twitter.

    Args:
        config: simulation config / configurazione simulazione
        simulation_dir: simulation directory / directory simulazione
        action_logger: action logger / logger azioni
        main_logger: main logger manager / gestore log principale
        max_rounds: max rounds (optional, truncates long runs) /
            round massimi (opzionale, tronca run lunghi)

    Returns:
        PlatformSimulation: result object with env and agent_graph /
        oggetto risultato con env e agent_graph
    """
    result = PlatformSimulation()
    
    def log_info(msg):
        if main_logger:
            main_logger.info(f"[Twitter] {msg}")
        print(f"[Twitter] {msg}")
    
    log_info("initializing / inizializzazione...")
    
    # Twitter uses generic LLM config.
    model = create_model(config, use_boost=False)
    
    # OASIS Twitter uses CSV profiles.
    profile_path = os.path.join(simulation_dir, "twitter_profiles.csv")
    if not os.path.exists(profile_path):
        log_info(f"error / errore: profile file not found / file profilo non trovato: {profile_path}")
        return result
    
    result.agent_graph = await generate_twitter_agent_graph(
        profile_path=profile_path,
        model=model,
        available_actions=TWITTER_ACTIONS,
    )
    
    # Load real Agent names from config (entity_name vs default Agent_X).
    agent_names = get_agent_names_from_config(config)
    # Fallback to OASIS default name when missing in config.
    for agent_id, agent in result.agent_graph.get_agents():
        if agent_id not in agent_names:
            agent_names[agent_id] = getattr(agent, 'name', f'Agent_{agent_id}')
    
    db_path = os.path.join(simulation_dir, "twitter_simulation.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    
    result.env = oasis.make(
        agent_graph=result.agent_graph,
        platform=oasis.DefaultPlatformType.TWITTER,
        database_path=db_path,
        semaphore=30,  # limit max concurrent LLM requests
    )
    
    await result.env.reset()
    log_info("environment started / ambiente avviato")
    
    if action_logger:
        action_logger.log_simulation_start(config)
    
    total_actions = 0
    last_rowid = 0  # track last processed rowid to avoid created_at format mismatch
    
    # Execute initial events.
    event_config = config.get("event_config", {})
    initial_posts = event_config.get("initial_posts", [])
    
    # Log round 0 start (initial events stage).
    if action_logger:
        action_logger.log_round_start(0, 0)  # round 0, simulated_hour 0
    
    initial_action_count = 0
    if initial_posts:
        initial_actions = {}
        for post in initial_posts:
            agent_id = post.get("poster_agent_id", 0)
            content = post.get("content", "")
            try:
                agent = result.env.agent_graph.get_agent(agent_id)
                initial_actions[agent] = ManualAction(
                    action_type=ActionType.CREATE_POST,
                    action_args={"content": content}
                )
                
                if action_logger:
                    action_logger.log_action(
                        round_num=0,
                        agent_id=agent_id,
                        agent_name=agent_names.get(agent_id, f"Agent_{agent_id}"),
                        action_type="CREATE_POST",
                        action_args={"content": content}
                    )
                    total_actions += 1
                    initial_action_count += 1
            except Exception:
                pass
        
        if initial_actions:
            await result.env.step(initial_actions)
            log_info(f"published initial posts / post iniziali pubblicati: {len(initial_actions)}")
    
            # Log round 0 end.
    if action_logger:
        action_logger.log_round_end(0, initial_action_count)
    
    # Main simulation loop.
    time_config = config.get("time_config", {})
    total_hours = time_config.get("total_simulation_hours", 72)
    minutes_per_round = time_config.get("minutes_per_round", 30)
    total_rounds = (total_hours * 60) // minutes_per_round
    
    # Truncate rounds if max_rounds is specified.
    if max_rounds is not None and max_rounds > 0:
        original_rounds = total_rounds
        total_rounds = min(total_rounds, max_rounds)
        if total_rounds < original_rounds:
            log_info(f"rounds truncated / round troncati: {original_rounds} -> {total_rounds} (max_rounds={max_rounds})")
    
    start_time = datetime.now()
    
    for round_num in range(total_rounds):
        # Check shutdown signal.
        if _shutdown_event and _shutdown_event.is_set():
            if main_logger:
                main_logger.info(f"shutdown signal received / segnale di arresto ricevuto, stopping at round {round_num + 1}")
            break
        
        simulated_minutes = round_num * minutes_per_round
        simulated_hour = (simulated_minutes // 60) % 24
        simulated_day = simulated_minutes // (60 * 24) + 1
        
        active_agents = get_active_agents_for_round(
            result.env, config, simulated_hour, round_num
        )
        
        # Always log round start, even with no active agents.
        if action_logger:
            action_logger.log_round_start(round_num + 1, simulated_hour)
        
        if not active_agents:
            # Also log round end when no active agents (actions_count=0).
            if action_logger:
                action_logger.log_round_end(round_num + 1, 0)
            continue
        
        actions = {agent: LLMAction() for _, agent in active_agents}
        await result.env.step(actions)
        
        # Fetch and log actual actions executed from DB.
        actual_actions, last_rowid = fetch_new_actions_from_db(
            db_path, last_rowid, agent_names
        )
        
        round_action_count = 0
        for action_data in actual_actions:
            if action_logger:
                action_logger.log_action(
                    round_num=round_num + 1,
                    agent_id=action_data['agent_id'],
                    agent_name=action_data['agent_name'],
                    action_type=action_data['action_type'],
                    action_args=action_data['action_args']
                )
                total_actions += 1
                round_action_count += 1
        
        if action_logger:
            action_logger.log_round_end(round_num + 1, round_action_count)
        
        if (round_num + 1) % 20 == 0:
            progress = (round_num + 1) / total_rounds * 100
            log_info(f"Day {simulated_day}, {simulated_hour:02d}:00 - Round {round_num + 1}/{total_rounds} ({progress:.1f}%)")
    
    # Do not close env here; keep it available for Interview.
    
    if action_logger:
        action_logger.log_simulation_end(total_rounds, total_actions)
    
    result.total_actions = total_actions
    elapsed = (datetime.now() - start_time).total_seconds()
    log_info(f"simulation loop complete / ciclo simulazione completato! elapsed / durata: {elapsed:.1f}s, total actions / azioni totali: {total_actions}")
    
    return result


async def run_reddit_simulation(
    config: Dict[str, Any], 
    simulation_dir: str,
    action_logger: Optional[PlatformActionLogger] = None,
    main_logger: Optional[SimulationLogManager] = None,
    max_rounds: Optional[int] = None
) -> PlatformSimulation:
    """Run Reddit simulation / Esegui simulazione Reddit.

    Args:
        config: simulation config / configurazione simulazione
        simulation_dir: simulation directory / directory simulazione
        action_logger: action logger / logger azioni
        main_logger: main logger manager / gestore log principale
        max_rounds: max rounds (optional, truncates long runs) /
            round massimi (opzionale, tronca run lunghi)

    Returns:
        PlatformSimulation: result object with env and agent_graph /
        oggetto risultato con env e agent_graph
    """
    result = PlatformSimulation()
    
    def log_info(msg):
        if main_logger:
            main_logger.info(f"[Reddit] {msg}")
        print(f"[Reddit] {msg}")
    
    log_info("initializing / inizializzazione...")
    
    # Reddit uses boost LLM config if available, otherwise generic.
    model = create_model(config, use_boost=True)
    
    profile_path = os.path.join(simulation_dir, "reddit_profiles.json")
    if not os.path.exists(profile_path):
        log_info(f"error / errore: profile file not found / file profilo non trovato: {profile_path}")
        return result
    
    result.agent_graph = await generate_reddit_agent_graph(
        profile_path=profile_path,
        model=model,
        available_actions=REDDIT_ACTIONS,
    )
    
    # Load real Agent names from config (entity_name vs default Agent_X).
    agent_names = get_agent_names_from_config(config)
    # Fallback to OASIS default name when missing in config.
    for agent_id, agent in result.agent_graph.get_agents():
        if agent_id not in agent_names:
            agent_names[agent_id] = getattr(agent, 'name', f'Agent_{agent_id}')
    
    db_path = os.path.join(simulation_dir, "reddit_simulation.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    
    result.env = oasis.make(
        agent_graph=result.agent_graph,
        platform=oasis.DefaultPlatformType.REDDIT,
        database_path=db_path,
        semaphore=30,  # limit max concurrent LLM requests
    )
    
    await result.env.reset()
    log_info("environment started / ambiente avviato")
    
    if action_logger:
        action_logger.log_simulation_start(config)
    
    total_actions = 0
    last_rowid = 0  # track last processed rowid to avoid created_at format mismatch
    
    # Execute initial events.
    event_config = config.get("event_config", {})
    initial_posts = event_config.get("initial_posts", [])
    
    # Log round 0 start (initial events stage).
    if action_logger:
        action_logger.log_round_start(0, 0)  # round 0, simulated_hour 0
    
    initial_action_count = 0
    if initial_posts:
        initial_actions = {}
        for post in initial_posts:
            agent_id = post.get("poster_agent_id", 0)
            content = post.get("content", "")
            try:
                agent = result.env.agent_graph.get_agent(agent_id)
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
                
                if action_logger:
                    action_logger.log_action(
                        round_num=0,
                        agent_id=agent_id,
                        agent_name=agent_names.get(agent_id, f"Agent_{agent_id}"),
                        action_type="CREATE_POST",
                        action_args={"content": content}
                    )
                    total_actions += 1
                    initial_action_count += 1
            except Exception:
                pass
        
        if initial_actions:
            await result.env.step(initial_actions)
            log_info(f"published initial posts / post iniziali pubblicati: {len(initial_actions)}")
    
            # Log round 0 end.
    if action_logger:
        action_logger.log_round_end(0, initial_action_count)
    
    # Main simulation loop.
    time_config = config.get("time_config", {})
    total_hours = time_config.get("total_simulation_hours", 72)
    minutes_per_round = time_config.get("minutes_per_round", 30)
    total_rounds = (total_hours * 60) // minutes_per_round
    
    # Truncate rounds if max_rounds is specified.
    if max_rounds is not None and max_rounds > 0:
        original_rounds = total_rounds
        total_rounds = min(total_rounds, max_rounds)
        if total_rounds < original_rounds:
            log_info(f"rounds truncated / round troncati: {original_rounds} -> {total_rounds} (max_rounds={max_rounds})")
    
    start_time = datetime.now()
    
    for round_num in range(total_rounds):
        # Check shutdown signal.
        if _shutdown_event and _shutdown_event.is_set():
            if main_logger:
                main_logger.info(f"shutdown signal received / segnale di arresto ricevuto, stopping at round {round_num + 1}")
            break
        
        simulated_minutes = round_num * minutes_per_round
        simulated_hour = (simulated_minutes // 60) % 24
        simulated_day = simulated_minutes // (60 * 24) + 1
        
        active_agents = get_active_agents_for_round(
            result.env, config, simulated_hour, round_num
        )
        
        # Always log round start, even with no active agents.
        if action_logger:
            action_logger.log_round_start(round_num + 1, simulated_hour)
        
        if not active_agents:
            # Also log round end when no active agents (actions_count=0).
            if action_logger:
                action_logger.log_round_end(round_num + 1, 0)
            continue
        
        actions = {agent: LLMAction() for _, agent in active_agents}
        await result.env.step(actions)
        
        # Fetch and log actual actions executed from DB.
        actual_actions, last_rowid = fetch_new_actions_from_db(
            db_path, last_rowid, agent_names
        )
        
        round_action_count = 0
        for action_data in actual_actions:
            if action_logger:
                action_logger.log_action(
                    round_num=round_num + 1,
                    agent_id=action_data['agent_id'],
                    agent_name=action_data['agent_name'],
                    action_type=action_data['action_type'],
                    action_args=action_data['action_args']
                )
                total_actions += 1
                round_action_count += 1
        
        if action_logger:
            action_logger.log_round_end(round_num + 1, round_action_count)
        
        if (round_num + 1) % 20 == 0:
            progress = (round_num + 1) / total_rounds * 100
            log_info(f"Day {simulated_day}, {simulated_hour:02d}:00 - Round {round_num + 1}/{total_rounds} ({progress:.1f}%)")
    
    # Do not close env here; keep it available for Interview.
    
    if action_logger:
        action_logger.log_simulation_end(total_rounds, total_actions)
    
    result.total_actions = total_actions
    elapsed = (datetime.now() - start_time).total_seconds()
    log_info(f"simulation loop complete / ciclo simulazione completato! elapsed / durata: {elapsed:.1f}s, total actions / azioni totali: {total_actions}")
    
    return result


async def main():
    parser = argparse.ArgumentParser(description='OASIS dual-platform parallel simulation / simulazione parallela dual-platform OASIS')
    parser.add_argument(
        '--config', 
        type=str, 
        required=True,
        help='config file path / percorso file configurazione (simulation_config.json)'
    )
    parser.add_argument(
        '--twitter-only',
        action='store_true',
        help='run Twitter simulation only / esegui solo simulazione Twitter'
    )
    parser.add_argument(
        '--reddit-only',
        action='store_true',
        help='run Reddit simulation only / esegui solo simulazione Reddit'
    )
    parser.add_argument(
        '--max-rounds',
        type=int,
        default=None,
        help='max simulation rounds (optional, truncates long runs) / round massimi (opzionale)'
    )
    parser.add_argument(
        '--no-wait',
        action='store_true',
        default=False,
        help='close env immediately after simulation; do not enter command-wait mode / chiudi subito ambiente dopo simulazione'
    )
    
    args = parser.parse_args()
    
    # Create shutdown event at main start so whole app reacts to termination signals.
    global _shutdown_event
    _shutdown_event = asyncio.Event()
    
    if not os.path.exists(args.config):
        print(f"error / errore: config file not found / file configurazione non trovato: {args.config}")
        sys.exit(1)
    
    config = load_config(args.config)
    simulation_dir = os.path.dirname(args.config) or "."
    wait_for_commands = not args.no_wait
    
    # Initialize log config (disable OASIS logs, clean old files).
    init_logging_for_simulation(simulation_dir)
    
    # Create log managers.
    log_manager = SimulationLogManager(simulation_dir)
    twitter_logger = log_manager.get_twitter_logger()
    reddit_logger = log_manager.get_reddit_logger()
    
    log_manager.info("=" * 60)
    log_manager.info("OASIS dual-platform parallel simulation / simulazione parallela dual-platform OASIS")
    log_manager.info(f"config file / file configurazione: {args.config}")
    log_manager.info(f"simulation ID / ID simulazione: {config.get('simulation_id', 'unknown')}")
    log_manager.info(f"command-wait mode / modalita attesa comandi: {'enabled / abilitata' if wait_for_commands else 'disabled / disabilitata'}")
    log_manager.info("=" * 60)
    
    time_config = config.get("time_config", {})
    total_hours = time_config.get('total_simulation_hours', 72)
    minutes_per_round = time_config.get('minutes_per_round', 30)
    config_total_rounds = (total_hours * 60) // minutes_per_round
    
    log_manager.info(f"simulation parameters / parametri simulazione:")
    log_manager.info(f"  - total duration / durata totale: {total_hours}h")
    log_manager.info(f"  - per-round duration / durata per round: {minutes_per_round}m")
    log_manager.info(f"  - configured total rounds / round totali da config: {config_total_rounds}")
    if args.max_rounds:
        log_manager.info(f"  - max rounds limit / limite round massimi: {args.max_rounds}")
        if args.max_rounds < config_total_rounds:
            log_manager.info(f"  - actual rounds / round effettivi: {args.max_rounds} (truncated / troncati)")
    log_manager.info(f"  - Agent count / numero Agent: {len(config.get('agent_configs', []))}")
    
    log_manager.info("log layout / struttura log:")
    log_manager.info(f"  - main log / log principale: simulation.log")
    log_manager.info(f"  - Twitter actions / azioni Twitter: twitter/actions.jsonl")
    log_manager.info(f"  - Reddit actions / azioni Reddit: reddit/actions.jsonl")
    log_manager.info("=" * 60)
    
    start_time = datetime.now()
    
    # Store simulation results for both platforms.
    twitter_result: Optional[PlatformSimulation] = None
    reddit_result: Optional[PlatformSimulation] = None
    
    if args.twitter_only:
        twitter_result = await run_twitter_simulation(config, simulation_dir, twitter_logger, log_manager, args.max_rounds)
    elif args.reddit_only:
        reddit_result = await run_reddit_simulation(config, simulation_dir, reddit_logger, log_manager, args.max_rounds)
    else:
        # Run in parallel (each platform uses its own logger).
        results = await asyncio.gather(
            run_twitter_simulation(config, simulation_dir, twitter_logger, log_manager, args.max_rounds),
            run_reddit_simulation(config, simulation_dir, reddit_logger, log_manager, args.max_rounds),
        )
        twitter_result, reddit_result = results
    
    total_elapsed = (datetime.now() - start_time).total_seconds()
    log_manager.info("=" * 60)
    log_manager.info(f"simulation loop complete / ciclo simulazione completato! total elapsed / durata totale: {total_elapsed:.1f}s")
    
    # Enter command-wait mode if requested.
    if wait_for_commands:
        log_manager.info("")
        log_manager.info("=" * 60)
        log_manager.info("entering command-wait mode / ingresso modalita attesa comandi - environment kept running / ambiente resta attivo")
        log_manager.info("supported commands / comandi supportati: interview, batch_interview, close_env")
        log_manager.info("=" * 60)
        
        # Create IPC handler.
        ipc_handler = ParallelIPCHandler(
            simulation_dir=simulation_dir,
            twitter_env=twitter_result.env if twitter_result else None,
            twitter_agent_graph=twitter_result.agent_graph if twitter_result else None,
            reddit_env=reddit_result.env if reddit_result else None,
            reddit_agent_graph=reddit_result.agent_graph if reddit_result else None
        )
        ipc_handler.update_status("alive")
        
        # Wait for commands loop (uses global _shutdown_event).
        try:
            while not _shutdown_event.is_set():
                should_continue = await ipc_handler.process_commands()
                if not should_continue:
                    break
                # Use wait_for instead of sleep so shutdown_event is reactive.
                try:
                    await asyncio.wait_for(_shutdown_event.wait(), timeout=0.5)
                    break  # shutdown signal received
                except asyncio.TimeoutError:
                    pass  # timeout, continue loop
        except KeyboardInterrupt:
            print("\ninterrupt signal received / segnale di interruzione ricevuto")
        except asyncio.CancelledError:
            print("\ntask cancelled / task annullato")
        except Exception as e:
            print(f"\ncommand handling error / errore gestione comandi: {e}")
        
        log_manager.info("\nclosing environment / chiusura ambiente...")
        ipc_handler.update_status("stopped")
    
    # Close environments.
    if twitter_result and twitter_result.env:
        await twitter_result.env.close()
        log_manager.info("[Twitter] environment closed / ambiente chiuso")
    
    if reddit_result and reddit_result.env:
        await reddit_result.env.close()
        log_manager.info("[Reddit] environment closed / ambiente chiuso")
    
    log_manager.info("=" * 60)
    log_manager.info(f"all done / completato!")
    log_manager.info(f"log files / file di log:")
    log_manager.info(f"  - {os.path.join(simulation_dir, 'simulation.log')}")
    log_manager.info(f"  - {os.path.join(simulation_dir, 'twitter', 'actions.jsonl')}")
    log_manager.info(f"  - {os.path.join(simulation_dir, 'reddit', 'actions.jsonl')}")
    log_manager.info("=" * 60)


def setup_signal_handlers(loop=None):
    """
    Configure signal handlers for graceful SIGTERM/SIGINT shutdown /
    Configura signal handler per shutdown pulito con SIGTERM/SIGINT.

    Persistent simulation mode keeps process alive after simulation to wait
    for interview commands. On termination signal, it should:
    1. notify asyncio loop to stop waiting
    2. allow normal cleanup (DB/env close, etc.)
    3. exit afterward
    """
    def signal_handler(signum, frame):
        global _cleanup_done
        sig_name = "SIGTERM" if signum == signal.SIGTERM else "SIGINT"
        print(f"\nreceived {sig_name}, shutting down / ricevuto {sig_name}, arresto in corso...")
        
        if not _cleanup_done:
            _cleanup_done = True
            # Notify asyncio loop to exit so resources can be cleaned.
            if _shutdown_event:
                _shutdown_event.set()
        
        # Avoid immediate sys.exit(); let asyncio close gracefully.
        # Force exit only if signal is received repeatedly.
        else:
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
        # Cleanup multiprocessing resource tracker (avoids shutdown warnings).
        try:
            from multiprocessing import resource_tracker
            resource_tracker._resource_tracker._stop()
        except Exception:
            pass
        print("simulation process exited / processo simulazione terminato")
