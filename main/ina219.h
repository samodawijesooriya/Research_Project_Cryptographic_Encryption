// main/ina219.h
#ifndef INA219_H
#define INA219_H

#include <stdint.h>
#include "driver/i2c.h"

void  ina219_init(i2c_port_t port, gpio_num_t sda, gpio_num_t scl, uint8_t addr);
float ina219_read_current_mA(void);
float ina219_read_bus_voltage_V(void);
float ina219_read_power_mW(void);

#endif // INA219_H