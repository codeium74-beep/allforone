"""API serveur pour monitoring et contrôle"""
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import time
from typing import Dict, List
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from monitoring.backend.metrics_collector import (
    MetricsCollector,
    HierarchyMetricsCollector,
    MissionMetricsCollector
)
from monitoring.backend.kill_switch import KillSwitchSystem, KillSwitchLevel

app = FastAPI(title="Matriarche Monitoring API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instances globales
system_metrics = MetricsCollector()
hierarchy_metrics = HierarchyMetricsCollector()
mission_metrics = MissionMetricsCollector()
kill_switch = KillSwitchSystem()

# WebSocket connections actives
active_connections: List[WebSocket] = []


@app.on_event("startup")
async def startup():
    """Démarrage du serveur"""
    print("[API] Server starting...")
    
    # Démarrage de la collecte de métriques
    asyncio.create_task(continuous_metrics_collection())


async def continuous_metrics_collection():
    """Collecte continue des métriques"""
    while True:
        try:
            # Collecte système
            sys_data = system_metrics.collect_system_metrics()
            system_metrics.store_metrics(sys_data)
            
            # Broadcast aux WebSockets
            await broadcast_metrics({
                'type': 'system_metrics',
                'data': sys_data
            })
            
            await asyncio.sleep(5)
            
        except Exception as e:
            print(f"[API] Error in metrics collection: {e}")
            await asyncio.sleep(10)


async def broadcast_metrics(data: Dict):
    """Broadcast vers tous les WebSockets actifs"""
    disconnected = []
    
    for connection in active_connections:
        try:
            await connection.send_json(data)
        except Exception:
            disconnected.append(connection)
    
    # Nettoyage des connexions mortes
    for conn in disconnected:
        active_connections.remove(conn)


@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """Stream temps réel des métriques"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Envoi périodique
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"[API] WebSocket error: {e}")
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)


@app.get("/api/status")
async def get_status():
    """Status global du système"""
    return {
        'timestamp': time.time(),
        'system': system_metrics.collect_system_metrics(),
        'hierarchy': hierarchy_metrics.get_hierarchy_summary(),
        'missions': mission_metrics.get_mission_stats(),
        'kill_switch': kill_switch.get_status()
    }


@app.get("/api/metrics/system")
async def get_system_metrics():
    """Métriques système actuelles"""
    return system_metrics.collect_system_metrics()


@app.get("/api/metrics/system/history")
async def get_system_history(count: int = 100):
    """Historique des métriques système"""
    return {
        'metrics': system_metrics.get_recent_metrics(count),
        'count': len(system_metrics.get_recent_metrics(count))
    }


@app.get("/api/metrics/system/average")
async def get_system_average(duration: int = 60):
    """Moyennes des métriques système"""
    return system_metrics.get_average_metrics(duration)


@app.get("/api/hierarchy/summary")
async def get_hierarchy_summary():
    """Résumé de la hiérarchie"""
    return hierarchy_metrics.get_hierarchy_summary()


@app.get("/api/hierarchy/matriarche")
async def get_matriarche_status():
    """Status de la Matriarche"""
    return hierarchy_metrics.matriarche_metrics


@app.get("/api/hierarchy/subs")
async def get_subs_status():
    """Status de toutes les Sous-Matriarches"""
    return {
        'subs': hierarchy_metrics.sub_matriarche_metrics,
        'count': len(hierarchy_metrics.sub_matriarche_metrics)
    }


@app.get("/api/hierarchy/protos")
async def get_protos_status():
    """Status de tous les Proto-Agents"""
    return {
        'protos': hierarchy_metrics.proto_metrics,
        'count': len(hierarchy_metrics.proto_metrics)
    }


@app.get("/api/missions")
async def get_missions():
    """Liste de toutes les missions"""
    return {
        'active': mission_metrics.active_missions,
        'completed': mission_metrics.completed_missions[-10:],  # 10 dernières
        'stats': mission_metrics.get_mission_stats()
    }


@app.post("/api/missions")
async def create_mission(mission: Dict):
    """Crée une nouvelle mission"""
    mission_id = mission.get('mission_id')
    
    if not mission_id:
        raise HTTPException(status_code=400, detail="mission_id required")
    
    mission_metrics.register_mission(mission_id, mission)
    
    return {
        'status': 'created',
        'mission_id': mission_id
    }


@app.get("/api/killswitch/status")
async def get_killswitch_status():
    """Status du Kill Switch"""
    return kill_switch.get_status()


@app.post("/api/killswitch/activate")
async def activate_killswitch(level: int, reason: str = "manual"):
    """Active manuellement le Kill Switch"""
    try:
        ks_level = KillSwitchLevel(level)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid level")
    
    asyncio.create_task(kill_switch.activate_level(ks_level, reason))
    
    return {
        'status': 'activated',
        'level': level,
        'level_name': ks_level.name
    }


@app.post("/api/killswitch/disarm")
async def disarm_killswitch():
    """Désarme le Kill Switch"""
    kill_switch.disarm()
    return {'status': 'disarmed'}


@app.post("/api/killswitch/rearm")
async def rearm_killswitch():
    """Réarme le Kill Switch"""
    kill_switch.rearm()
    return {'status': 'rearmed'}


@app.get("/api/network/stats")
async def get_network_stats():
    """Statistiques réseau"""
    return system_metrics.collect_network_metrics()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'timestamp': time.time()
    }


if __name__ == '__main__':
    import uvicorn
    
    print("Starting Monitoring API Server...")
    print("Access at: http://localhost:8000")
    print("Docs at: http://localhost:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
