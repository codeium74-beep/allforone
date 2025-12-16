"""Communications furtives - DNS, ICMP, Steganography, HTTP Mimicry"""
from .dns_tunnel import DNSTunnel
from .icmp_tunnel import ICMPTunnel
from .image_stego import ImageSteganography
from .http_mimicry import HTTPMimicry

__all__ = ['DNSTunnel', 'ICMPTunnel', 'ImageSteganography', 'HTTPMimicry']
