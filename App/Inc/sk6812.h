#ifndef _LED_DRIVER_SK6812
#define _LED_DRIVER_SK6812


#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>
#include <stdbool.h>


// LED parameters
 #define NUM_BPP (3) // WS2812B
//#define NUM_BPP (4) // SK6812
#define NUM_PIXELS (35)

void led_set_RGB(uint8_t index, uint8_t r, uint8_t g, uint8_t b);
void led_set_RGBW(uint8_t index, uint8_t r, uint8_t g, uint8_t b, uint8_t w);
void led_set_all_RGB(uint8_t r, uint8_t g, uint8_t b);
void led_set_all_RGBW(uint8_t r, uint8_t g, uint8_t b, uint8_t w);
void led_render();

bool is_transfer_ongoing();

#ifdef __cplusplus
}
#endif

#endif
