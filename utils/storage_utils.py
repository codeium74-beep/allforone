"""Utilitaires pour stockage distribué et redondant"""
import os
import json
import hashlib
import lz4.frame
import msgpack
from typing import Dict, List, Optional, Any
from pathlib import Path
import shutil


class DistributedStorage:
    """Système de stockage distribué avec sharding et réplication"""
    
    def __init__(self, base_path: str, replication_factor: int = 5):
        self.base_path = Path(base_path)
        self.replication_factor = replication_factor
        self.shard_size = 256 * 1024  # 256KB par shard
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Sous-répertoires pour organisation
        self.data_dir = self.base_path / "data"
        self.index_dir = self.base_path / "index"
        self.metadata_dir = self.base_path / "metadata"
        
        for dir_path in [self.data_dir, self.index_dir, self.metadata_dir]:
            dir_path.mkdir(exist_ok=True)
    
    def store(self, content_id: str, data: bytes, compress: bool = True) -> Dict:
        """Stocke des données avec sharding et réplication"""
        if compress:
            data = lz4.frame.compress(data)
        
        # Calcul hash pour vérification intégrité
        data_hash = hashlib.sha256(data).hexdigest()
        
        # Sharding
        shards = self._shard_data(data)
        shard_infos = []
        
        for i, shard in enumerate(shards):
            shard_id = f"{content_id}_shard_{i}"
            shard_hash = hashlib.sha256(shard).hexdigest()
            
            # Réplication
            replicas = self._replicate_shard(shard_id, shard)
            
            shard_infos.append({
                'shard_id': shard_id,
                'shard_index': i,
                'shard_hash': shard_hash,
                'shard_size': len(shard),
                'replicas': replicas
            })
        
        # Métadonnées
        metadata = {
            'content_id': content_id,
            'data_hash': data_hash,
            'original_size': len(data),
            'compressed': compress,
            'shard_count': len(shards),
            'shards': shard_infos,
            'replication_factor': self.replication_factor
        }
        
        # Sauvegarde métadonnées
        self._save_metadata(content_id, metadata)
        
        return metadata
    
    def retrieve(self, content_id: str) -> Optional[bytes]:
        """Récupère des données depuis le stockage distribué"""
        # Chargement métadonnées
        metadata = self._load_metadata(content_id)
        if not metadata:
            return None
        
        # Récupération shards
        shards = []
        for shard_info in metadata['shards']:
            shard = self._retrieve_shard(shard_info)
            if shard is None:
                return None  # Échec si un shard manque
            shards.append(shard)
        
        # Réassemblage
        data = b''.join(shards)
        
        # Vérification hash
        if hashlib.sha256(data).hexdigest() != metadata['data_hash']:
            raise ValueError("Data integrity check failed")
        
        # Décompression si nécessaire
        if metadata['compressed']:
            data = lz4.frame.decompress(data)
        
        return data
    
    def delete(self, content_id: str):
        """Supprime des données et toutes leurs répliques"""
        metadata = self._load_metadata(content_id)
        if not metadata:
            return
        
        # Suppression de tous les shards et répliques
        for shard_info in metadata['shards']:
            for replica_path in shard_info['replicas']:
                try:
                    os.remove(replica_path)
                except FileNotFoundError:
                    pass
        
        # Suppression métadonnées
        metadata_path = self.metadata_dir / f"{content_id}.meta"
        try:
            os.remove(metadata_path)
        except FileNotFoundError:
            pass
    
    def verify_integrity(self, content_id: str) -> Dict[str, Any]:
        """Vérifie l'intégrité des données stockées"""
        metadata = self._load_metadata(content_id)
        if not metadata:
            return {'status': 'not_found'}
        
        results = {
            'content_id': content_id,
            'status': 'ok',
            'missing_replicas': [],
            'corrupted_shards': []
        }
        
        for shard_info in metadata['shards']:
            # Vérification existence répliques
            valid_replicas = 0
            for replica_path in shard_info['replicas']:
                if os.path.exists(replica_path):
                    # Vérification hash
                    with open(replica_path, 'rb') as f:
                        shard_data = f.read()
                    
                    if hashlib.sha256(shard_data).hexdigest() == shard_info['shard_hash']:
                        valid_replicas += 1
                    else:
                        results['corrupted_shards'].append(replica_path)
            
            if valid_replicas < self.replication_factor:
                results['missing_replicas'].append({
                    'shard_id': shard_info['shard_id'],
                    'expected': self.replication_factor,
                    'found': valid_replicas
                })
        
        if results['missing_replicas'] or results['corrupted_shards']:
            results['status'] = 'degraded'
        
        return results
    
    def repair(self, content_id: str):
        """Répare les données en recréant les répliques manquantes"""
        integrity = self.verify_integrity(content_id)
        if integrity['status'] == 'ok':
            return
        
        metadata = self._load_metadata(content_id)
        
        for shard_info in metadata['shards']:
            # Trouve une réplique valide
            valid_shard_data = None
            for replica_path in shard_info['replicas']:
                if os.path.exists(replica_path):
                    with open(replica_path, 'rb') as f:
                        data = f.read()
                    if hashlib.sha256(data).hexdigest() == shard_info['shard_hash']:
                        valid_shard_data = data
                        break
            
            if valid_shard_data:
                # Recrée les répliques manquantes
                missing_count = self.replication_factor - len([
                    p for p in shard_info['replicas'] if os.path.exists(p)
                ])
                
                for _ in range(missing_count):
                    new_replica_path = self._generate_replica_path(shard_info['shard_id'])
                    with open(new_replica_path, 'wb') as f:
                        f.write(valid_shard_data)
                    shard_info['replicas'].append(str(new_replica_path))
        
        # Sauvegarde métadonnées mises à jour
        self._save_metadata(content_id, metadata)
    
    def _shard_data(self, data: bytes) -> List[bytes]:
        """Divise les données en shards"""
        shards = []
        for i in range(0, len(data), self.shard_size):
            shards.append(data[i:i+self.shard_size])
        return shards
    
    def _replicate_shard(self, shard_id: str, shard_data: bytes) -> List[str]:
        """Crée plusieurs répliques d'un shard"""
        replica_paths = []
        
        for i in range(self.replication_factor):
            replica_path = self._generate_replica_path(shard_id, i)
            with open(replica_path, 'wb') as f:
                f.write(shard_data)
            replica_paths.append(str(replica_path))
        
        return replica_paths
    
    def _generate_replica_path(self, shard_id: str, replica_index: int = None) -> Path:
        """Génère un chemin pour une réplique"""
        if replica_index is None:
            import random
            replica_index = random.randint(0, 999999)
        
        # Organisation en sous-répertoires (évite trop de fichiers par dossier)
        subdir = hashlib.md5(shard_id.encode()).hexdigest()[:2]
        target_dir = self.data_dir / subdir
        target_dir.mkdir(exist_ok=True)
        
        return target_dir / f"{shard_id}_replica_{replica_index}.shard"
    
    def _retrieve_shard(self, shard_info: Dict) -> Optional[bytes]:
        """Récupère un shard depuis ses répliques"""
        for replica_path in shard_info['replicas']:
            if os.path.exists(replica_path):
                with open(replica_path, 'rb') as f:
                    data = f.read()
                
                # Vérification hash
                if hashlib.sha256(data).hexdigest() == shard_info['shard_hash']:
                    return data
        
        return None
    
    def _save_metadata(self, content_id: str, metadata: Dict):
        """Sauvegarde les métadonnées"""
        metadata_path = self.metadata_dir / f"{content_id}.meta"
        with open(metadata_path, 'wb') as f:
            f.write(msgpack.packb(metadata))
    
    def _load_metadata(self, content_id: str) -> Optional[Dict]:
        """Charge les métadonnées"""
        metadata_path = self.metadata_dir / f"{content_id}.meta"
        if not metadata_path.exists():
            return None
        
        with open(metadata_path, 'rb') as f:
            return msgpack.unpackb(f.read(), raw=False)
    
    def get_storage_stats(self) -> Dict:
        """Obtient les statistiques de stockage"""
        total_size = 0
        file_count = 0
        
        for root, dirs, files in os.walk(self.base_path):
            for file in files:
                file_path = os.path.join(root, file)
                total_size += os.path.getsize(file_path)
                file_count += 1
        
        metadata_count = len(list(self.metadata_dir.glob("*.meta")))
        
        return {
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'file_count': file_count,
            'content_count': metadata_count,
            'base_path': str(self.base_path)
        }


class KnowledgeGraph:
    """Graphe de connaissances compact pour stockage d'informations"""
    
    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.graph_file = self.storage_path / "knowledge_graph.msgpack"
        
        # Structure: {node_id: {attributes}, ...}, [(from, to, relation), ...]
        self.nodes = {}
        self.edges = []
        
        self._load()
    
    def add_node(self, node_id: str, attributes: Dict):
        """Ajoute un nœud au graphe"""
        self.nodes[node_id] = attributes
        self._save()
    
    def add_edge(self, from_id: str, to_id: str, relation: str):
        """Ajoute une arête au graphe"""
        self.edges.append((from_id, to_id, relation))
        self._save()
    
    def get_node(self, node_id: str) -> Optional[Dict]:
        """Récupère un nœud"""
        return self.nodes.get(node_id)
    
    def get_neighbors(self, node_id: str) -> List[Tuple[str, str]]:
        """Récupère les voisins d'un nœud"""
        neighbors = []
        for from_id, to_id, relation in self.edges:
            if from_id == node_id:
                neighbors.append((to_id, relation))
        return neighbors
    
    def query(self, node_type: Optional[str] = None) -> List[Dict]:
        """Requête sur les nœuds"""
        if node_type is None:
            return list(self.nodes.values())
        
        return [
            attrs for attrs in self.nodes.values()
            if attrs.get('type') == node_type
        ]
    
    def _save(self):
        """Sauvegarde le graphe"""
        data = {
            'nodes': self.nodes,
            'edges': self.edges
        }
        with open(self.graph_file, 'wb') as f:
            f.write(msgpack.packb(data))
    
    def _load(self):
        """Charge le graphe"""
        if self.graph_file.exists():
            with open(self.graph_file, 'rb') as f:
                data = msgpack.unpackb(f.read(), raw=False)
                self.nodes = data['nodes']
                self.edges = data['edges']
