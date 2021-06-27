#include "stdio.h"
#include "usart.h"
#include "Uart_fifo/UartTxFifo.h"

#ifdef __GNUC__
#define PUTCAHR_PROTOTYPE int __io_putchar(int ch)
#define GETCHAR_PROTOTYPE int __io_getchar(void)
#else
#define PUTCAHR_PROTOTYPE int fputc(int ch, FILE *f)
#define GETCHAR_PROTOTYPE int fgetc(FILE *f)
#endif /* __GNUC__ */

int _write(int file, char *ptr, int len)
{
	return UartTxFifo_write(&debugLogTx, (uint8_t*) ptr, len);
}
