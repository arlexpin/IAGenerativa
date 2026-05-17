import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.herramientas import verificar_elegibilidad, generar_etiqueta_devolucion
from src.agente_devoluciones import parse_return_request, fallback_return_flow


def test_verificar_elegibilidad_higiene_sin_usar():
    res = verificar_elegibilidad(producto_id='PROD-003', estado_producto='sin usar')
    assert isinstance(res, dict)
    assert res.get('elegible') is True


def test_verificar_elegibilidad_higiene_usado():
    res = verificar_elegibilidad(producto_id='PROD-004', estado_producto='usado')
    assert isinstance(res, dict)
    assert res.get('elegible') is False


def test_verificar_elegibilidad_perecedero():
    res = verificar_elegibilidad(producto_id='PROD-005', estado_producto='nuevo')
    assert isinstance(res, dict)
    assert res.get('elegible') is False


def test_generar_etiqueta():
    etiqueta = generar_etiqueta_devolucion(pedido_id='EM-900', producto_id='PROD-001', direccion_cliente='Calle 1')
    assert isinstance(etiqueta, dict)
    assert 'codigo_seguimiento' in etiqueta
    assert 'etiqueta_url' in etiqueta


def test_parse_return_request_full():
    texto = 'Quiero devolver PROD-003 del pedido EM-904. Dirección: Calle 123, Cali. Está sin usar.'
    parsed = parse_return_request(texto)
    assert parsed['producto_id'] == 'PROD-003'
    assert parsed['pedido_id'] == 'EM-904'
    assert 'Calle 123' in parsed['direccion_cliente']
    assert parsed['estado_producto'] == 'sin usar'


def test_fallback_flow_complete():
    texto = 'Mi pedido EM-904, devolver PROD-003, direccion Calle 123'
    out = fallback_return_flow(texto)
    assert isinstance(out, str)
    assert 'Generé la etiqueta' in out or 'etiqueta' in out


if __name__ == '__main__':
    tests = [
        test_verificar_elegibilidad_higiene_sin_usar,
        test_verificar_elegibilidad_higiene_usado,
        test_verificar_elegibilidad_perecedero,
        test_generar_etiqueta,
        test_parse_return_request_full,
        test_fallback_flow_complete,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"OK: {t.__name__}")
        except AssertionError as e:
            print(f"FAIL: {t.__name__} -> {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR: {t.__name__} -> {e}")
            failed += 1
    if failed:
        print(f"{failed} tests failed")
        sys.exit(1)
    print("All tests passed")
