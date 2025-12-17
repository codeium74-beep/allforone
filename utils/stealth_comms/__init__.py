"""Stealth communication modules - Covert channels for data exfiltration"""
from .dns_tunnel import DNSTunnel, DNSExfiltrator
from .icmp_tunnel import ICMPTunnel, ICMPExfiltrator, PingCovertChannel
from .image_stego import ImageSteganography, AdvancedSteganography
from .http_mimicry import HTTPMimicry, HTTPExfiltrator

__all__ = [
    'DNSTunnel',
    'DNSExfiltrator',
    'ICMPTunnel',
    'ICMPExfiltrator',
    'PingCovertChannel',
    'ImageSteganography',
    'AdvancedSteganography',
    'HTTPMimicry',
    'HTTPExfiltrator'
]
