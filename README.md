# CAN Scripts

This repository contains two main scripts for manipulating and visualizing CAN data:

1. `can_chart.py`

## can_chart.py

This script processes CAN data files and generates charts for truck speed, engine RPM, and CM system status. Current supported SPNs:

| SPN   | Description                    |
|-------|--------------------------------|
| 84    | Wheel-Based Vehicle Speed      |
| 190   | Engine Speed                   |
| 5676  | Advanced Emergency Braking System Status |

### Usage

1. Place the `.txt` data files in the `data` directory or in subdirectories within it.
   * The candump format must be the following:
   ```
    (1735835558.169416) can0 0CF00203#DC0000FFF40000FF
    (1735835558.169742) can0 08F11027#C70FFFFFFFFFFFFF
    (1735835558.170030) can0 0CF02903#90B37CFFFFFFFFFF
    ```

2. Run the script:

    ```sh
    python can_chart.py
    ```

### Dependencies

- `matplotlib`
- `numpy`

To install the dependencies, run:

```sh
pip install matplotlib numpy
```