# 🕹️ JoyBridge 3D (or your chosen name)

An educational hardware-in-the-loop project that bridges 2D/3D game software with real-world embedded controllers. The project follows a deliberate progression path: starting with traditional keyboard control, moving to a wired Arduino controller over a virtual serial port, and finalizing as a standalone, battery-powered wireless controller using an ESP32 over Bluetooth Low Energy (BLE).

The entire framework relies on a decoupled architecture—meaning the inner game logic remains stable while the underlying transport layer dynamically changes.

## 🚀 Key Features

* **Multi-Engine Workspace:** Features a lightweight 2D collision prototype built in Pygame and a richer 3D orbit-camera environment built in Ursina.
* **Hardware Interfacing:** Reads real-time multi-axis analog potentiometer voltages and stable digital switch actions (`INPUT_PULLUP`).
* **Custom Packet Engineering:** Utilizes a strict, lightweight comma-delimited data contract (`J1_X,J1_Y,J1_SW...`) passed via standard 115200 baud UART frames.
* **Wireless BLE Architecture:** Upgrades the physical USB pipeline into a notify-characteristic layout driven by an independent ESP32 peripheral runtime.

## 🛠️ Tech Stack & Skills Highlighted

* **Software:** Python 3.14+, Pygame-CE, Ursina Engine, pySerial.
* **Hardware:** Arduino Uno, ESP32, Analog Joystick Modules.
* **Core Concepts:** Game Loop Architecture, Frame-Independent Movement (dt), Multi-threaded Serial Input Buffers, Analog-to-Digital Conversion (ADC), Bluetooth Core Profiles.
