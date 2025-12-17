"""
Proxmox Integration - Gestion des ressources via Proxmox VE
Permet l'allocation dynamique de CPU/RAM et la gestion des VMs
"""
import time
from typing import Dict, List, Optional
from proxmoxer import ProxmoxAPI
import logging


class ProxmoxManager:
    """
    Gestionnaire d'intégration Proxmox
    
    Fonctionnalités:
    - Connexion à l'API Proxmox
    - Liste et gestion des VMs
    - Allocation dynamique de ressources
    - Snapshots et clonage
    - Monitoring des ressources
    """
    
    def __init__(self, host: str, user: str, password: str, verify_ssl: bool = False):
        """
        Args:
            host: Hôte Proxmox (ex: proxmox.local)
            user: Utilisateur (ex: root@pam)
            password: Mot de passe
            verify_ssl: Vérifier SSL
        """
        self.host = host
        self.user = user
        self.proxmox = None
        self.connected = False
        
        try:
            self.proxmox = ProxmoxAPI(
                host,
                user=user,
                password=password,
                verify_ssl=verify_ssl
            )
            self.connected = True
            logging.info(f"[ProxmoxManager] Connected to {host}")
        except Exception as e:
            logging.error(f"[ProxmoxManager] Connection failed: {e}")
            self.connected = False
    
    def connect(self) -> bool:
        """
        Teste la connexion à Proxmox
        
        Returns:
            True si connecté
        """
        if not self.connected:
            logging.error("[ProxmoxManager] Not connected")
            return False
        
        try:
            # Test de connexion via requête version
            version = self.proxmox.version.get()
            logging.info(f"[ProxmoxManager] Proxmox version: {version['version']}")
            return True
        except Exception as e:
            logging.error(f"[ProxmoxManager] Connection test failed: {e}")
            return False
    
    def list_nodes(self) -> List[Dict]:
        """
        Liste les nœuds Proxmox
        
        Returns:
            Liste des nœuds
        """
        if not self.connected:
            return []
        
        try:
            nodes = self.proxmox.nodes.get()
            logging.info(f"[ProxmoxManager] Found {len(nodes)} nodes")
            return nodes
        except Exception as e:
            logging.error(f"[ProxmoxManager] Failed to list nodes: {e}")
            return []
    
    def list_vms(self, node: Optional[str] = None) -> List[Dict]:
        """
        Liste les VMs
        
        Args:
            node: Nœud spécifique (optionnel)
        
        Returns:
            Liste des VMs
        """
        if not self.connected:
            return []
        
        try:
            all_vms = []
            
            if node:
                # VMs d'un nœud spécifique
                vms = self.proxmox.nodes(node).qemu.get()
                all_vms.extend(vms)
            else:
                # VMs de tous les nœuds
                nodes = self.list_nodes()
                for n in nodes:
                    vms = self.proxmox.nodes(n['node']).qemu.get()
                    all_vms.extend(vms)
            
            logging.info(f"[ProxmoxManager] Found {len(all_vms)} VMs")
            return all_vms
            
        except Exception as e:
            logging.error(f"[ProxmoxManager] Failed to list VMs: {e}")
            return []
    
    def get_vm_status(self, node: str, vmid: int) -> Optional[Dict]:
        """
        Récupère le statut d'une VM
        
        Args:
            node: Nœud
            vmid: ID de la VM
        
        Returns:
            Statut de la VM
        """
        if not self.connected:
            return None
        
        try:
            status = self.proxmox.nodes(node).qemu(vmid).status.current.get()
            return status
        except Exception as e:
            logging.error(f"[ProxmoxManager] Failed to get VM {vmid} status: {e}")
            return None
    
    def update_vm_resources(self, node: str, vmid: int, 
                           cpu_cores: Optional[int] = None,
                           memory_mb: Optional[int] = None) -> bool:
        """
        Met à jour les ressources d'une VM
        
        Args:
            node: Nœud
            vmid: ID de la VM
            cpu_cores: Nombre de cœurs CPU
            memory_mb: Mémoire en MB
        
        Returns:
            True si succès
        """
        if not self.connected:
            return False
        
        try:
            config = {}
            
            if cpu_cores is not None:
                config['cores'] = cpu_cores
            
            if memory_mb is not None:
                config['memory'] = memory_mb
            
            if not config:
                logging.warning("[ProxmoxManager] No resources to update")
                return False
            
            # Mise à jour de la configuration
            self.proxmox.nodes(node).qemu(vmid).config.put(**config)
            
            logging.info(f"[ProxmoxManager] Updated VM {vmid} resources: {config}")
            return True
            
        except Exception as e:
            logging.error(f"[ProxmoxManager] Failed to update VM {vmid}: {e}")
            return False
    
    def create_snapshot(self, node: str, vmid: int, snapname: str, 
                       description: str = "") -> bool:
        """
        Crée un snapshot d'une VM
        
        Args:
            node: Nœud
            vmid: ID de la VM
            snapname: Nom du snapshot
            description: Description
        
        Returns:
            True si succès
        """
        if not self.connected:
            return False
        
        try:
            self.proxmox.nodes(node).qemu(vmid).snapshot.post(
                snapname=snapname,
                description=description or f"Snapshot created at {time.time()}"
            )
            
            logging.info(f"[ProxmoxManager] Created snapshot '{snapname}' for VM {vmid}")
            return True
            
        except Exception as e:
            logging.error(f"[ProxmoxManager] Failed to create snapshot: {e}")
            return False
    
    def rollback_snapshot(self, node: str, vmid: int, snapname: str) -> bool:
        """
        Restaure un snapshot
        
        Args:
            node: Nœud
            vmid: ID de la VM
            snapname: Nom du snapshot
        
        Returns:
            True si succès
        """
        if not self.connected:
            return False
        
        try:
            self.proxmox.nodes(node).qemu(vmid).snapshot(snapname).rollback.post()
            
            logging.info(f"[ProxmoxManager] Rolled back to snapshot '{snapname}' for VM {vmid}")
            return True
            
        except Exception as e:
            logging.error(f"[ProxmoxManager] Failed to rollback snapshot: {e}")
            return False
    
    def clone_vm(self, node: str, vmid: int, newid: int, name: str,
                 full: bool = True) -> bool:
        """
        Clone une VM
        
        Args:
            node: Nœud
            vmid: ID source
            newid: Nouvel ID
            name: Nom du clone
            full: Clone complet (sinon linked clone)
        
        Returns:
            True si succès
        """
        if not self.connected:
            return False
        
        try:
            self.proxmox.nodes(node).qemu(vmid).clone.post(
                newid=newid,
                name=name,
                full=1 if full else 0
            )
            
            logging.info(f"[ProxmoxManager] Cloned VM {vmid} to {newid} (name: {name})")
            return True
            
        except Exception as e:
            logging.error(f"[ProxmoxManager] Failed to clone VM: {e}")
            return False
    
    def start_vm(self, node: str, vmid: int) -> bool:
        """Démarre une VM"""
        if not self.connected:
            return False
        
        try:
            self.proxmox.nodes(node).qemu(vmid).status.start.post()
            logging.info(f"[ProxmoxManager] Started VM {vmid}")
            return True
        except Exception as e:
            logging.error(f"[ProxmoxManager] Failed to start VM {vmid}: {e}")
            return False
    
    def stop_vm(self, node: str, vmid: int) -> bool:
        """Arrête une VM"""
        if not self.connected:
            return False
        
        try:
            self.proxmox.nodes(node).qemu(vmid).status.stop.post()
            logging.info(f"[ProxmoxManager] Stopped VM {vmid}")
            return True
        except Exception as e:
            logging.error(f"[ProxmoxManager] Failed to stop VM {vmid}: {e}")
            return False
    
    def get_node_resources(self, node: str) -> Optional[Dict]:
        """
        Récupère les ressources d'un nœud
        
        Args:
            node: Nom du nœud
        
        Returns:
            Ressources du nœud
        """
        if not self.connected:
            return None
        
        try:
            status = self.proxmox.nodes(node).status.get()
            
            resources = {
                'cpu_used': status.get('cpu', 0),
                'cpu_total': status.get('maxcpu', 0),
                'memory_used': status.get('memory', 0),
                'memory_total': status.get('maxmem', 0),
                'memory_used_percent': (status.get('memory', 0) / status.get('maxmem', 1)) * 100,
                'uptime': status.get('uptime', 0)
            }
            
            return resources
            
        except Exception as e:
            logging.error(f"[ProxmoxManager] Failed to get node resources: {e}")
            return None


class DynamicResourceAllocator:
    """
    Allocateur dynamique de ressources basé sur PoW/PoM
    """
    
    def __init__(self, proxmox_manager: ProxmoxManager):
        self.proxmox = proxmox_manager
        self.allocations = {}  # {agent_id: {node, vmid, resources}}
    
    def allocate_resources(self, agent_id: str, cpu_cores: int, memory_mb: int,
                          node: Optional[str] = None) -> Optional[Dict]:
        """
        Alloue des ressources pour un agent
        
        Args:
            agent_id: ID de l'agent
            cpu_cores: Cœurs CPU demandés
            memory_mb: Mémoire demandée
            node: Nœud spécifique (optionnel)
        
        Returns:
            Détails de l'allocation ou None
        """
        # Sélection d'un nœud si non spécifié
        if not node:
            nodes = self.proxmox.list_nodes()
            if not nodes:
                logging.error("[DynamicResourceAllocator] No nodes available")
                return None
            
            # Sélection du nœud avec le plus de ressources disponibles
            best_node = None
            max_available = 0
            
            for n in nodes:
                resources = self.proxmox.get_node_resources(n['node'])
                if resources:
                    available = resources['memory_total'] - resources['memory_used']
                    if available > max_available:
                        max_available = available
                        best_node = n['node']
            
            node = best_node
        
        if not node:
            logging.error("[DynamicResourceAllocator] No suitable node found")
            return None
        
        # Recherche ou création d'une VM pour l'agent
        # Pour simplifier, on suppose que les VMs sont pré-créées
        vms = self.proxmox.list_vms(node)
        
        if not vms:
            logging.error(f"[DynamicResourceAllocator] No VMs available on {node}")
            return None
        
        # Sélection d'une VM (première VM disponible pour simplification)
        vm = vms[0]
        vmid = vm['vmid']
        
        # Mise à jour des ressources
        success = self.proxmox.update_vm_resources(node, vmid, cpu_cores, memory_mb)
        
        if success:
            allocation = {
                'agent_id': agent_id,
                'node': node,
                'vmid': vmid,
                'cpu_cores': cpu_cores,
                'memory_mb': memory_mb,
                'allocated_at': time.time()
            }
            
            self.allocations[agent_id] = allocation
            
            logging.info(f"[DynamicResourceAllocator] Allocated resources to {agent_id}: {allocation}")
            return allocation
        
        return None
    
    def deallocate_resources(self, agent_id: str) -> bool:
        """Libère les ressources d'un agent"""
        if agent_id not in self.allocations:
            return False
        
        allocation = self.allocations[agent_id]
        
        # Réduction des ressources (optionnel)
        # Pour l'instant, on marque simplement comme libéré
        
        del self.allocations[agent_id]
        
        logging.info(f"[DynamicResourceAllocator] Deallocated resources for {agent_id}")
        return True
    
    def get_allocation(self, agent_id: str) -> Optional[Dict]:
        """Récupère l'allocation d'un agent"""
        return self.allocations.get(agent_id)


if __name__ == '__main__':
    # Test de l'intégration Proxmox
    print("=== Proxmox Integration Test ===\n")
    
    # Configuration (à adapter)
    config = {
        'host': 'proxmox.local',
        'user': 'root@pam',
        'password': 'your_password',
        'verify_ssl': False
    }
    
    print("Note: This test requires a running Proxmox VE instance")
    print("Update the config with your Proxmox credentials\n")
    
    # Test basique
    try:
        manager = ProxmoxManager(**config)
        
        if manager.connect():
            print("✓ Connected to Proxmox")
            
            # Liste des nœuds
            nodes = manager.list_nodes()
            print(f"\nNodes: {len(nodes)}")
            for node in nodes:
                print(f"  - {node['node']}: {node['status']}")
            
            # Liste des VMs
            if nodes:
                vms = manager.list_vms(nodes[0]['node'])
                print(f"\nVMs on {nodes[0]['node']}: {len(vms)}")
                for vm in vms[:3]:
                    print(f"  - VM {vm['vmid']}: {vm['name']} ({vm['status']})")
        else:
            print("✗ Failed to connect to Proxmox")
    
    except Exception as e:
        print(f"✗ Test failed: {e}")
        print("\nThis is expected if Proxmox is not configured")
    
    print("\n✓ Test complete")
