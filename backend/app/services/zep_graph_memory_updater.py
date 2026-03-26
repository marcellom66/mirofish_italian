"""
Zep graph memory update service / Servizio di aggiornamento memoria grafo Zep.
Dynamically updates agent activities from simulations into the Zep graph /
Aggiorna dinamicamente nel grafo Zep le attivita degli agenti dalle simulazioni.
"""

import os
import time
import threading
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from queue import Queue, Empty

from zep_cloud.client import Zep

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.zep_graph_memory_updater')


@dataclass
class AgentActivity:
    """Agent activity record / registro attivita agente"""
    platform: str           # twitter / reddit
    agent_id: int
    agent_name: str
    action_type: str        # CREATE_POST, LIKE_POST, etc.
    action_args: Dict[str, Any]
    round_num: int
    timestamp: str
    
    def to_episode_text(self) -> str:
        """
        Convert activity into text that can be sent to Zep / Converte l attivita in testo inviabile a Zep
        
        Use natural-language descriptions so Zep can extract entities and relations / Usa descrizioni in linguaggio naturale affinche Zep estragga entita e relazioni
        Do not add simulation-specific prefixes to avoid misleading graph updates / Non aggiungere prefissi della simulazione per evitare aggiornamenti fuorvianti del grafo
        """
        # generate different descriptions by action type / genera descrizioni diverse per tipo di azione
        action_descriptions = {
            "CREATE_POST": self._describe_create_post,
            "LIKE_POST": self._describe_like_post,
            "DISLIKE_POST": self._describe_dislike_post,
            "REPOST": self._describe_repost,
            "QUOTE_POST": self._describe_quote_post,
            "FOLLOW": self._describe_follow,
            "CREATE_COMMENT": self._describe_create_comment,
            "LIKE_COMMENT": self._describe_like_comment,
            "DISLIKE_COMMENT": self._describe_dislike_comment,
            "SEARCH_POSTS": self._describe_search,
            "SEARCH_USER": self._describe_search_user,
            "MUTE": self._describe_mute,
        }
        
        describe_func = action_descriptions.get(self.action_type, self._describe_generic)
        description = describe_func()
        
        # return "agent name: activity description" format directly, without simulation prefix / restituisce direttamente il formato "nome agente: descrizione attivita", senza prefisso simulazione
        return f"{self.agent_name}: {description}"
    
    def _describe_create_post(self) -> str:
        content = self.action_args.get("content", "")
        if content:
            return f"published a post / ha pubblicato un post: \"{content}\""
        return "published a post / ha pubblicato un post"

    def _describe_like_post(self) -> str:
        """Like post - includes original post text and author info / Mi piace al post - include testo originale e autore"""
        post_content = self.action_args.get("post_content", "")
        post_author = self.action_args.get("post_author_name", "")

        if post_content and post_author:
            return f"liked {post_author}'s post / ha messo mi piace al post di {post_author}: \"{post_content}\""
        if post_content:
            return f"liked a post / ha messo mi piace a un post: \"{post_content}\""
        if post_author:
            return f"liked a post by {post_author} / ha messo mi piace a un post di {post_author}"
        return "liked a post / ha messo mi piace a un post"

    def _describe_dislike_post(self) -> str:
        """Dislike post - includes original post text and author info / Non mi piace al post - include testo originale e autore"""
        post_content = self.action_args.get("post_content", "")
        post_author = self.action_args.get("post_author_name", "")

        if post_content and post_author:
            return f"disliked {post_author}'s post / non ha apprezzato il post di {post_author}: \"{post_content}\""
        if post_content:
            return f"disliked a post / non ha apprezzato un post: \"{post_content}\""
        if post_author:
            return f"disliked a post by {post_author} / non ha apprezzato un post di {post_author}"
        return "disliked a post / non ha apprezzato un post"

    def _describe_repost(self) -> str:
        """Repost - includes original post content and author info / Repost - include contenuto e autore originali"""
        original_content = self.action_args.get("original_content", "")
        original_author = self.action_args.get("original_author_name", "")

        if original_content and original_author:
            return f"reposted {original_author}'s post / ha ripubblicato il post di {original_author}: \"{original_content}\""
        if original_content:
            return f"reposted a post / ha ripubblicato un post: \"{original_content}\""
        if original_author:
            return f"reposted a post by {original_author} / ha ripubblicato un post di {original_author}"
        return "reposted a post / ha ripubblicato un post"

    def _describe_quote_post(self) -> str:
        """Quote post - includes original post, author, and quote comment / Cita post - include post originale, autore e commento di citazione"""
        original_content = self.action_args.get("original_content", "")
        original_author = self.action_args.get("original_author_name", "")
        quote_content = self.action_args.get("quote_content", "") or self.action_args.get("content", "")

        if original_content and original_author:
            base = f"quoted {original_author}'s post / ha citato il post di {original_author}: \"{original_content}\""
        elif original_content:
            base = f"quoted a post / ha citato un post: \"{original_content}\""
        elif original_author:
            base = f"quoted a post by {original_author} / ha citato un post di {original_author}"
        else:
            base = "quoted a post / ha citato un post"

        if quote_content:
            base += f"; and commented / e ha commentato: \"{quote_content}\""
        return base

    def _describe_follow(self) -> str:
        """Follow user - includes followed user name / Segui utente - include nome utente seguito"""
        target_user_name = self.action_args.get("target_user_name", "")

        if target_user_name:
            return f"followed user {target_user_name} / ha seguito l'utente {target_user_name}"
        return "followed a user / ha seguito un utente"

    def _describe_create_comment(self) -> str:
        """Create comment - includes comment content and target post info / Crea commento - include contenuto e info del post target"""
        content = self.action_args.get("content", "")
        post_content = self.action_args.get("post_content", "")
        post_author = self.action_args.get("post_author_name", "")

        if content:
            if post_content and post_author:
                return f"commented on {post_author}'s post / ha commentato il post di {post_author}: \"{post_content}\"; comment: \"{content}\""
            if post_content:
                return f"commented on a post / ha commentato un post: \"{post_content}\"; comment: \"{content}\""
            if post_author:
                return f"commented on a post by {post_author} / ha commentato un post di {post_author}: \"{content}\""
            return f"commented / ha commentato: \"{content}\""
        return "published a comment / ha pubblicato un commento"

    def _describe_like_comment(self) -> str:
        """Like comment - includes comment content and author info / Mi piace al commento - include contenuto e autore"""
        comment_content = self.action_args.get("comment_content", "")
        comment_author = self.action_args.get("comment_author_name", "")

        if comment_content and comment_author:
            return f"liked {comment_author}'s comment / ha messo mi piace al commento di {comment_author}: \"{comment_content}\""
        if comment_content:
            return f"liked a comment / ha messo mi piace a un commento: \"{comment_content}\""
        if comment_author:
            return f"liked a comment by {comment_author} / ha messo mi piace a un commento di {comment_author}"
        return "liked a comment / ha messo mi piace a un commento"

    def _describe_dislike_comment(self) -> str:
        """Dislike comment - includes comment content and author info / Non mi piace al commento - include contenuto e autore"""
        comment_content = self.action_args.get("comment_content", "")
        comment_author = self.action_args.get("comment_author_name", "")

        if comment_content and comment_author:
            return f"disliked {comment_author}'s comment / non ha apprezzato il commento di {comment_author}: \"{comment_content}\""
        if comment_content:
            return f"disliked a comment / non ha apprezzato un commento: \"{comment_content}\""
        if comment_author:
            return f"disliked a comment by {comment_author} / non ha apprezzato un commento di {comment_author}"
        return "disliked a comment / non ha apprezzato un commento"

    def _describe_search(self) -> str:
        """Search posts - includes search keyword / Cerca post - include parola chiave"""
        query = self.action_args.get("query", "") or self.action_args.get("keyword", "")
        return f"searched for \"{query}\" / ha cercato \"{query}\"" if query else "performed a search / ha eseguito una ricerca"

    def _describe_search_user(self) -> str:
        """Search users - includes search keyword / Cerca utenti - include parola chiave"""
        query = self.action_args.get("query", "") or self.action_args.get("username", "")
        return f"searched for user \"{query}\" / ha cercato l'utente \"{query}\"" if query else "searched for a user / ha cercato un utente"

    def _describe_mute(self) -> str:
        """Mute user - includes muted user name / Silenzia utente - include nome utente silenziato"""
        target_user_name = self.action_args.get("target_user_name", "")

        if target_user_name:
            return f"muted user {target_user_name} / ha silenziato l'utente {target_user_name}"
        return "muted a user / ha silenziato un utente"

    def _describe_generic(self) -> str:
        # for unknown action types, generate a generic description / per tipi azione sconosciuti, genera una descrizione generica
        return f"performed {self.action_type} action / ha eseguito l'azione {self.action_type}"


class ZepGraphMemoryUpdater:
    """
    Zep graph memory updater / aggiornatore memoria grafo Zep
    
    Monitors simulation actions logs and updates new agent activities to Zep graph in real time / Monitora i log azioni della simulazione e aggiorna in tempo reale le nuove attivita agente nel grafo Zep
    Groups by platform and sends in batches each time BATCH_SIZE activities are accumulated / Raggruppa per piattaforma e invia in batch ogni volta che si accumulano BATCH_SIZE attivita
    
    All meaningful actions are updated to Zep; action_args contains full context: / Tutte le azioni significative vengono aggiornate su Zep; action_args contiene il contesto completo:
    - liked/disliked post original text / testo originale del post messo mi piace/non mi piace
    - reposted/quoted post original text / testo originale del post repostato/citato
    - followed/muted usernames / nomi utente seguiti/silenziati
    - liked/disliked comment original text / testo originale del commento messo mi piace/non mi piace
    """
    
    # batch send size (how many to accumulate per platform before send) / dimensione invio batch (quante attivita accumulare per piattaforma prima dell invio)
    BATCH_SIZE = 5
    
    # platform display name mapping (for console output) / mappatura nomi piattaforma (per output console)
    PLATFORM_DISPLAY_NAMES = {
        'twitter': 'World 1 / Mondo 1',
        'reddit': 'World 2 / Mondo 2',
    }
    
    # send interval (seconds), avoids sending too fast / intervallo invio (secondi), evita richieste troppo rapide
    SEND_INTERVAL = 0.5
    
    # retry configuration / configurazione retry
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # sec / s
    
    def __init__(self, graph_id: str, api_key: Optional[str] = None):
        """
        Initialize updater / Inizializza updater
        
        Args:
            graph_id: Zep graph ID / ID grafo Zep
            api_key: Zep API key (optional, default from config) / chiave API Zep (opzionale, default da configurazione)
        """
        self.graph_id = graph_id
        self.api_key = api_key or Config.ZEP_API_KEY
        
        if not self.api_key:
            raise ValueError("ZEP_API_KEY not configured / ZEP_API_KEY non configurata")
        
        self.client = Zep(api_key=self.api_key)
        
        # activity queue / coda attivita
        self._activity_queue: Queue = Queue()
        
        # platform-grouped activity buffers (each platform sends once BATCH_SIZE is reached) / buffer attivita per piattaforma (ogni piattaforma invia al raggiungimento di BATCH_SIZE)
        self._platform_buffers: Dict[str, List[AgentActivity]] = {
            'twitter': [],
            'reddit': [],
        }
        self._buffer_lock = threading.Lock()
        
        # control flags / flag di controllo
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        
        # stats / statistiche
        self._total_activities = 0  # activities actually enqueued / numero attivita realmente accodate
        self._total_sent = 0        # batches successfully sent to Zep / numero batch inviati con successo a Zep
        self._total_items_sent = 0  # activities successfully sent to Zep / numero attivita inviate con successo a Zep
        self._failed_count = 0      # failed batch sends / numero batch con invio fallito
        self._skipped_count = 0     # filtered and skipped activities (DO_NOTHING) / attivita filtrate e saltate (DO_NOTHING)
        
        logger.info(f"ZepGraphMemoryUpdater initialization completed / inizializzazione completata: graph_id={graph_id}, batch_size={self.BATCH_SIZE}")
    
    def _get_platform_display_name(self, platform: str) -> str:
        """get platform display name / ottieni nome visualizzato piattaforma"""
        return self.PLATFORM_DISPLAY_NAMES.get(platform.lower(), platform)
    
    def start(self):
        """start background worker thread / avvia thread worker in background"""
        if self._running:
            return
        
        self._running = True
        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            daemon=True,
            name=f"ZepMemoryUpdater-{self.graph_id[:8]}"
        )
        self._worker_thread.start()
        logger.info(f"ZepGraphMemoryUpdater started / avviato: graph_id={self.graph_id}")
    
    def stop(self):
        """stop background worker thread / ferma thread worker in background"""
        self._running = False
        
        # send remaining activities / invia attivita residue
        self._flush_remaining()
        
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=10)
        
        logger.info(f"ZepGraphMemoryUpdater stopped / fermato: graph_id={self.graph_id}, "
                   f"total_activities={self._total_activities}, "
                   f"batches_sent={self._total_sent}, "
                   f"items_sent={self._total_items_sent}, "
                   f"failed={self._failed_count}, "
                   f"skipped={self._skipped_count}")
    
    def add_activity(self, activity: AgentActivity):
        """
        add one agent activity to queue / aggiungi un attivita agente alla coda
        
        All meaningful actions are enqueued, including: / Tutte le azioni significative vengono accodate, incluse:
        - CREATE_POST（post creation / creazione post）
        - CREATE_COMMENT（comment creation / creazione commento）
        - QUOTE_POST（quote post / cita post）
        - SEARCH_POSTS（search posts / cerca post）
        - SEARCH_USER（search users / cerca utenti）
        - LIKE_POST/DISLIKE_POST（like/dislike posts / mi piace/non mi piace post）
        - REPOST（repost / repost）
        - FOLLOW（follow / segui）
        - MUTE（mute / silenzia）
        - LIKE_COMMENT/DISLIKE_COMMENT (like/dislike comments / mi piace/non mi piace commenti)
        
        action_args contains full context (e.g., post text, usernames, etc.) / action_args contiene il contesto completo (es. testo post, nomi utente, ecc.)
        
        Args:
            activity: Agent activity record / registro attivita agente
        """
        # skip DO_NOTHING activities / salta le attivita DO_NOTHING
        if activity.action_type == "DO_NOTHING":
            self._skipped_count += 1
            return
        
        self._activity_queue.put(activity)
        self._total_activities += 1
        logger.debug(f"added activity to Zep queue / attivita aggiunta alla coda Zep: {activity.agent_name} - {activity.action_type}")
    
    def add_activity_from_dict(self, data: Dict[str, Any], platform: str):
        """
        add activity from dictionary data / aggiungi attivita da dati dizionario
        
        Args:
            data: dictionary parsed from actions.jsonl / dizionario parsato da actions.jsonl
            platform: platform name (twitter/reddit) / nome piattaforma (twitter/reddit)
        """
        # skip event-type entries / salta voci di tipo evento
        if "event_type" in data:
            return
        
        activity = AgentActivity(
            platform=platform,
            agent_id=data.get("agent_id", 0),
            agent_name=data.get("agent_name", ""),
            action_type=data.get("action_type", ""),
            action_args=data.get("action_args", {}),
            round_num=data.get("round", 0),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
        )
        
        self.add_activity(activity)
    
    def _worker_loop(self):
        """background worker loop - send activities to Zep in platform batches / ciclo worker in background - invia attivita a Zep in batch per piattaforma"""
        while self._running or not self._activity_queue.empty():
            try:
                # try to get activity from queue (1s timeout) / prova a leggere attivita dalla coda (timeout 1s)
                try:
                    activity = self._activity_queue.get(timeout=1)
                    
                    # add activity to the corresponding platform buffer / aggiungi attivita al buffer della piattaforma corrispondente
                    platform = activity.platform.lower()
                    with self._buffer_lock:
                        if platform not in self._platform_buffers:
                            self._platform_buffers[platform] = []
                        self._platform_buffers[platform].append(activity)
                        
                        # check whether this platform reached batch size / verifica se questa piattaforma ha raggiunto la dimensione batch
                        if len(self._platform_buffers[platform]) >= self.BATCH_SIZE:
                            batch = self._platform_buffers[platform][:self.BATCH_SIZE]
                            self._platform_buffers[platform] = self._platform_buffers[platform][self.BATCH_SIZE:]
                            # send after releasing lock / invia dopo aver rilasciato il lock
                            self._send_batch_activities(batch, platform)
                            # send interval to avoid too-fast requests / intervallo invio per evitare richieste troppo rapide
                            time.sleep(self.SEND_INTERVAL)
                    
                except Empty:
                    pass
                    
            except Exception as e:
                logger.error(f"worker loop exception / eccezione ciclo worker: {e}")
                time.sleep(1)
    
    def _send_batch_activities(self, activities: List[AgentActivity], platform: str):
        """
        send activities to Zep graph in batch (combined as one text) / invia attivita al grafo Zep in batch (combinate in un unico testo)
        
        Args:
            activities: Agent activity list / lista attivita agente
            platform: platform name / nome piattaforma
        """
        if not activities:
            return
        
        # combine multiple activities into one text, separated by newlines / combina piu attivita in un unico testo, separate da newline
        episode_texts = [activity.to_episode_text() for activity in activities]
        combined_text = "\n".join(episode_texts)
        
        # send with retries / invio con retry
        for attempt in range(self.MAX_RETRIES):
            try:
                self.client.graph.add(
                    graph_id=self.graph_id,
                    type="text",
                    data=combined_text
                )
                
                self._total_sent += 1
                self._total_items_sent += len(activities)
                display_name = self._get_platform_display_name(platform)
                logger.info(
                    f"successfully sent in batch / inviato con successo in batch: "
                    f"{len(activities)} items / elementi from {display_name} to graph / al grafo {self.graph_id}"
                )
                logger.debug(f"batch content preview / anteprima contenuto batch: {combined_text[:200]}...")
                return
                
            except Exception as e:
                if attempt < self.MAX_RETRIES - 1:
                    logger.warning(f"batch send to Zep failed / invio batch a Zep fallito (attempt / tentativo {attempt + 1}/{self.MAX_RETRIES}): {e}")
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
                else:
                    logger.error(
                        f"batch send to Zep failed after retries / invio batch a Zep fallito dopo i retry "
                        f"({self.MAX_RETRIES} times / volte): {e}"
                    )
                    self._failed_count += 1
    
    def _flush_remaining(self):
        """send remaining activities in queue and buffers / invia attivita residue in coda e buffer"""
        # first process remaining queue activities and add to buffers / prima processa le attivita residue in coda e aggiungile ai buffer
        while not self._activity_queue.empty():
            try:
                activity = self._activity_queue.get_nowait()
                platform = activity.platform.lower()
                with self._buffer_lock:
                    if platform not in self._platform_buffers:
                        self._platform_buffers[platform] = []
                    self._platform_buffers[platform].append(activity)
            except Empty:
                break
        
        # then send remaining activities in each platform buffer (even if below BATCH_SIZE)
        # poi invia le attivita residue in ogni buffer piattaforma (anche se sotto BATCH_SIZE)
        with self._buffer_lock:
            for platform, buffer in self._platform_buffers.items():
                if buffer:
                    display_name = self._get_platform_display_name(platform)
                    logger.info(
                        f"send remaining activities for {display_name} platform / "
                        f"invia attivita residue per la piattaforma {display_name}: {len(buffer)} items / elementi"
                    )
                    self._send_batch_activities(buffer, platform)
            # clear all buffers / svuota tutti i buffer
            for platform in self._platform_buffers:
                self._platform_buffers[platform] = []
    
    def get_stats(self) -> Dict[str, Any]:
        """get statistics / ottieni statistiche"""
        with self._buffer_lock:
            buffer_sizes = {p: len(b) for p, b in self._platform_buffers.items()}
        
        return {
            "graph_id": self.graph_id,
            "batch_size": self.BATCH_SIZE,
            "total_activities": self._total_activities,  # total enqueued activities / totale attivita accodate
            "batches_sent": self._total_sent,            # successful batch sends / numero batch inviati con successo
            "items_sent": self._total_items_sent,        # successful sent activities / numero attivita inviate con successo
            "failed_count": self._failed_count,          # failed batch sends / numero batch con invio fallito
            "skipped_count": self._skipped_count,        # filtered and skipped activities (DO_NOTHING) / attivita filtrate e saltate (DO_NOTHING)
            "queue_size": self._activity_queue.qsize(),
            "buffer_sizes": buffer_sizes,                # per-platform buffer sizes / dimensioni buffer per piattaforma
            "running": self._running,
        }


class ZepGraphMemoryManager:
    """
    manage multiple simulation Zep graph memory updaters / gestisce piu updater memoria grafo Zep per simulazione
    
    each simulation can have its own updater instance / ogni simulazione puo avere la propria istanza updater
    """
    
    _updaters: Dict[str, ZepGraphMemoryUpdater] = {}
    _lock = threading.Lock()
    
    @classmethod
    def create_updater(cls, simulation_id: str, graph_id: str) -> ZepGraphMemoryUpdater:
        """
        create graph memory updater for simulation / crea updater memoria grafo per simulazione
        
        Args:
            simulation_id: simulation ID / ID simulazione
            graph_id: Zep graph ID / ID grafo Zep
            
        Returns:
            ZepGraphMemoryUpdater instance / istanza ZepGraphMemoryUpdater
        """
        with cls._lock:
            # if it already exists, stop the old one first / se esiste gia, ferma prima quello precedente
            if simulation_id in cls._updaters:
                cls._updaters[simulation_id].stop()
            
            updater = ZepGraphMemoryUpdater(graph_id)
            updater.start()
            cls._updaters[simulation_id] = updater
            
            logger.info(f"created graph memory updater / creato updater memoria grafo: simulation_id={simulation_id}, graph_id={graph_id}")
            return updater
    
    @classmethod
    def get_updater(cls, simulation_id: str) -> Optional[ZepGraphMemoryUpdater]:
        """get simulation updater / ottieni updater della simulazione"""
        return cls._updaters.get(simulation_id)
    
    @classmethod
    def stop_updater(cls, simulation_id: str):
        """stop and remove simulation updater / ferma e rimuovi updater della simulazione"""
        with cls._lock:
            if simulation_id in cls._updaters:
                cls._updaters[simulation_id].stop()
                del cls._updaters[simulation_id]
                logger.info(f"stopped graph memory updater / updater memoria grafo fermato: simulation_id={simulation_id}")
    
    # flag to prevent duplicate stop_all calls / flag per evitare chiamate duplicate a stop_all
    _stop_all_done = False
    
    @classmethod
    def stop_all(cls):
        """stop all updaters / ferma tutti gli updater"""
        # prevent duplicate calls / evita chiamate duplicate
        if cls._stop_all_done:
            return
        cls._stop_all_done = True
        
        with cls._lock:
            if cls._updaters:
                for simulation_id, updater in list(cls._updaters.items()):
                    try:
                        updater.stop()
                    except Exception as e:
                        logger.error(f"failed to stop updater / arresto updater fallito: simulation_id={simulation_id}, error={e}")
                cls._updaters.clear()
            logger.info("stopped all graph memory updaters / fermati tutti gli updater memoria grafo")
    
    @classmethod
    def get_all_stats(cls) -> Dict[str, Dict[str, Any]]:
        """get statistics for all updaters / ottieni statistiche di tutti gli updater"""
        return {
            sim_id: updater.get_stats() 
            for sim_id, updater in cls._updaters.items()
        }
