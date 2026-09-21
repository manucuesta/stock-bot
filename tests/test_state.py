from src.state import (
    get_source_state,
    load_state,
    save_state,
    update_source_state,
)


SOURCE_ID = "test-product"


def reset():
    state = {
        "states": {}
    }
    save_state(state)
    return state


def show_state(state):
    print(
        "Estado:",
        get_source_state(state, SOURCE_ID)
    )


print("\n=== TEST 1: producto inicialmente agotado ===")

state = reset()

update_source_state(
    state,
    SOURCE_ID,
    qualifies=False,
    price=None,
)

save_state(state)

show_state(state)


print("\n=== TEST 2: aparece stock a 99.99 € ===")

state = load_state()

previous = get_source_state(
    state,
    SOURCE_ID,
)

previous_qualifies = previous.get(
    "qualifies",
    False,
)

current_qualifies = True

if current_qualifies and not previous_qualifies:
    print("🚨 ALERTA: producto disponible")

update_source_state(
    state,
    SOURCE_ID,
    qualifies=True,
    price=99.99,
)

save_state(state)

show_state(state)


print("\n=== TEST 3: sigue disponible a 99.99 € ===")

state = load_state()

previous = get_source_state(
    state,
    SOURCE_ID,
)

previous_qualifies = previous.get(
    "qualifies",
    False,
)

current_qualifies = True

if current_qualifies and not previous_qualifies:
    print("🚨 ALERTA")
else:
    print("✅ Sin alerta: ya estaba disponible")

update_source_state(
    state,
    SOURCE_ID,
    qualifies=True,
    price=99.99,
)

save_state(state)

show_state(state)


print("\n=== TEST 4: vuelve a agotarse ===")

state = load_state()

update_source_state(
    state,
    SOURCE_ID,
    qualifies=False,
    price=None,
)

save_state(state)

print("🔴 Producto agotado")

show_state(state)


print("\n=== TEST 5: vuelve a aparecer ===")

state = load_state()

previous = get_source_state(
    state,
    SOURCE_ID,
)

previous_qualifies = previous.get(
    "qualifies",
    False,
)

current_qualifies = True

if current_qualifies and not previous_qualifies:
    print("🚨 ALERTA: volvió a estar disponible")

update_source_state(
    state,
    SOURCE_ID,
    qualifies=True,
    price=104.99,
)

save_state(state)

show_state(state)