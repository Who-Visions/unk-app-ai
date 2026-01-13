# Repo Analysis: Flumine

Role: `Executor`
URL: https://github.com/betcode-org/flumine.git

## ML and Data Signals
- Signals: None detected
- Notebooks: True
- Data dir: False

## Integration Signals (top files)
- README.md (score 4)
- docs\index.md (score 4)
- docs\quickstart.md (score 4)
- examples\example-betconnect.py (score 4)
- examples\example-sportsdata.py (score 4)
- tests\test_clients.py (score 4)
- tests\test_order.py (score 4)
- flumine\clients\baseclient.py (score 4)
- docs\clients.md (score 3)
- docs\controls.md (score 3)
- docs\sportsdata.md (score 3)
- examples\example-single.py (score 3)
- examples\example.py (score 3)
- examples\marketrecorder.py (score 3)
- examples\tennisexample.py (score 3)

## Prompt and Persona Definitions (hits)
- `flumine\execution\betdaqexecution.py`
  - Excerpt: `they can be picked back up\n            for order in order_package:\n                with order.trade:\n                    order.executable()\n\n    def update(self, order_package: BaseOrderPackage):\n        # temp copy to prevent an empty list of instructions sent\n        # this can occur if order is matched during the execution\n        order_list = list(order_package.update_instructions)\n        if not order_list:\n            logger.warning("Empty `order_list`", extra=order_package.info)`
- `flumine\execution\betfairexecution.py`
  - Excerpt: `ransaction(len(order_package))\n\n    def place(self, order_package: BaseOrderPackage, session: requests.Session):\n        return order_package.client.betting_client.betting.place_orders(\n            market_id=order_package.market_id,\n            instructions=order_package.place_instructions,\n            customer_ref=order_package.id.hex,\n            market_version=order_package.market_version,\n            customer_strategy_ref=order_package.customer_strategy_ref,\n            async_=order_package.asy`
- `flumine\order\order.py`
  - Excerpt: `float = None) -> None:\n        raise NotImplementedError\n\n    def update(self, new_persistence_type: str) -> None:\n        raise NotImplementedError\n\n    def replace(self, new_price: float) -> None:\n        raise NotImplementedError\n\n    # instructions\n    def create_place_instruction(self) -> dict:\n        raise NotImplementedError\n\n    def create_cancel_instruction(self) -> dict:\n        raise NotImplementedError\n\n    def create_update_instruction(self) -> dict:\n        raise NotImplemen`

Unk = Uncle
Target: 35+ users
