from src.monitor import qualifies


SOURCE = {
    "id": "test-price",
    "name": "Producto de prueba",
    "price_max": 110,
}


def test(price, status="available"):
    result = {
        "status": status,
        "price": price,
    }

    valid = qualifies(SOURCE, result)

    print(
        f"precio={price} | status={status} | "
        f"{'🟢 CUMPLE' if valid else '🔴 NO CUMPLE'}"
    )


print("\n=== TEST LÍMITE DE PRECIO ===")

test(120)
test(111)
test(110)
test(109)
test(None)

print("\n=== TEST PRODUCTO NO DISPONIBLE ===")

test(99, "not_qualified")
test(99, "unknown")