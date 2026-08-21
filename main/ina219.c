// main/ina219.c
#include "ina219.h"
#include <string.h>

#define REG_CONFIG      0x00
#define REG_SHUNT_V     0x01
#define REG_BUS_V       0x02
#define REG_POWER       0x03
#define REG_CURRENT     0x04
#define REG_CALIBRATION 0x05

// Rshunt = 0.1 ohm ("R100" on the PCB). Current_LSB chosen so the
// calibration register is an integer, per the datasheet formula:
//   Cal = trunc(0.04096 / (Current_LSB * Rshunt))
#define CURRENT_LSB_MA   0.1f     // 100 uA per bit
#define CAL_VALUE        4096
#define POWER_LSB_MW      (20.0f * CURRENT_LSB_MA)   // datasheet: Power_LSB = 20 x Current_LSB

static i2c_port_t s_port;
static uint8_t    s_addr;

static void write_reg16(uint8_t reg, uint16_t value) {
    uint8_t buf[3] = { reg, (uint8_t)(value >> 8), (uint8_t)(value & 0xFF) };
    i2c_master_write_to_device(s_port, s_addr, buf, sizeof(buf), pdMS_TO_TICKS(100));
}

static int16_t read_reg16(uint8_t reg) {
    uint8_t rx[2] = {0};
    i2c_master_write_read_device(s_port, s_addr, &reg, 1, rx, 2, pdMS_TO_TICKS(100));
    return (int16_t)((rx[0] << 8) | rx[1]);
}

void ina219_init(i2c_port_t port, gpio_num_t sda, gpio_num_t scl, uint8_t addr) {
    s_port = port;
    s_addr = addr;

    i2c_config_t conf = {
        .mode = I2C_MODE_MASTER,
        .sda_io_num = sda,
        .scl_io_num = scl,
        .sda_pullup_en = GPIO_PULLUP_ENABLE,
        .scl_pullup_en = GPIO_PULLUP_ENABLE,
        .master.clk_speed = 400000,
    };
    i2c_param_config(port, &conf);
    i2c_driver_install(port, conf.mode, 0, 0, 0);

    write_reg16(REG_CALIBRATION, CAL_VALUE);

    // Bus voltage range 32V, gain /8 (PGA), 12-bit ADC, continuous shunt+bus
    // sampling — standard "high range" config for a 5V rail with headroom.
    uint16_t config = 0x399F;
    write_reg16(REG_CONFIG, config);
}

float ina219_read_current_mA(void) {
    return (float)read_reg16(REG_CURRENT) * CURRENT_LSB_MA;
}

float ina219_read_bus_voltage_V(void) {
    int16_t raw = read_reg16(REG_BUS_V);
    raw >>= 3;                 // low 3 bits are status flags, not voltage data
    return raw * 0.004f;       // bus voltage LSB = 4 mV
}

float ina219_read_power_mW(void) {
    return (float)read_reg16(REG_POWER) * POWER_LSB_MW;
}