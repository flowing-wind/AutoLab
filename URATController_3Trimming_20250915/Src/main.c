/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2023 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

#include "string.h"
#include "stdlib.h"
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
TIM_HandleTypeDef htim1;

UART_HandleTypeDef huart1;

/* USER CODE BEGIN PV */
#define RXBUFFERSIZE  1024     


//如果需要开启print，就取消DEBUG注释
#define DEBUG 
	
char rec_buffer[RXBUFFERSIZE];   
char mode[128];
char setting[1024];



uint8_t Uart1_Rx_Cnt = 0;		
uint8_t aRxBuffer;	



// 定义16位位域结构体
typedef struct {
    unsigned int R3_IN0 : 1;  // 最低位 (Bit 0)
    unsigned int R3_IN1 : 1;  // Bit 1
    unsigned int R3_IN2 : 1;  // Bit 2
    unsigned int R3_IN3 : 1;  // Bit 3
    unsigned int R2_IN0 : 1;  // Bit 4
    unsigned int R2_IN1 : 1;  // Bit 5
    unsigned int R2_IN2 : 1;  // Bit 6
    unsigned int R2_IN3 : 1;  // Bit 7
    unsigned int R1_IN0 : 1;  // Bit 8
    unsigned int R1_IN1 : 1;  // Bit 9
    unsigned int R1_IN2 : 1;  // Bit 10
    unsigned int R1_IN3 : 1;  // Bit 11
    unsigned int LDO0  : 1;   // Bit 12
    unsigned int LDO1  : 1;   // Bit 13
    unsigned int LDO2  : 1;   // Bit 14
    unsigned int LDO3  : 1;   // 最高位 (Bit 15)
} TrimBits16;

typedef union {
    uint16_t value;
    TrimBits16 bits;
} TrimRegister16;
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_USART1_UART_Init(void);
static void MX_TIM1_Init(void);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
#include "stdio.h"
#ifdef __GNUC__
#define PUTCHAR_PROTOTYPE int __io_putchar(int ch)
#else
#define PUTCHAR_PROTOTYPE int fputc(int ch, FILE *f)
#endif
PUTCHAR_PROTOTYPE
{
    HAL_UART_Transmit(&huart1 , (uint8_t *)&ch, 1, 0xFFFF);
    return ch;
}
int fgetc(FILE *f)
{
  uint8_t ch = 0;
  HAL_UART_Receive(&huart1, &ch, 1, 0xffff);
  return ch;
}


/**
 * @brief 分割字符串函数
 * @param str 输入字符串
 * @param strLen 输入字符串长度
 * @param splitChar 分隔符字符串
 * @param index 要获取的分段索引（从1开始）
 * @param result 存储结果的缓冲区
 * @param maxLen 结果缓冲区的最大长度
 * @return 成功返回分段长度，失败返回错误码
 */
int split(const char* str, int strLen, const char* splitChar, int index, char* result, int maxLen)
{
    int i = 0;              // 循环索引
    int ret = 0;            // 返回值
    int findLen = 0;        // 可搜索的长度
    int findFlag = 0;       // 查找状态标志
    int startIndex = 0;     // 分段起始位置
    int splitCharLen = 0;   // 分隔符长度

    // 参数检查：输入字符串、结果缓冲区、分隔符不能为空，索引必须大于0
    if(NULL == str || NULL == result || NULL == splitChar || index <= 0)
    {
        return -1;  // 参数错误
    }      
    
    // 获取分隔符长度
    splitCharLen = strlen(splitChar);
    
    // 计算可搜索的长度（总长度减去分隔符长度）
    findLen = strLen - splitCharLen;
    if(findLen < 0)
    {
        return -2;  // 字符串长度不足
    }  
   
    // 遍历字符串查找分隔符
    for(; i <= findLen && str[i] != '\0'; i++)
    {
        // 检查当前位置是否匹配分隔符
        if(strncmp(&str[i], splitChar, splitCharLen) == 0)
        {
            if(0 == findFlag)  // 第一次找到分隔符（查找左边界）
            {
                startIndex++;  // 分隔符计数增加
                
                if(1 == index)  // 如果是第一个分段
                {
                    // 复制从开始到当前分隔符之前的内容
                    strncpy(result, &str[0], i);
                    ret = i;    // 返回分段长度
                    break;      // 结束循环
                }
                else if(startIndex + 1 == index)  // 找到目标分段的前一个分隔符
                {
                    startIndex = i;  // 记录分段起始位置（当前分隔符位置）
                    findFlag = 1;    // 设置标志，表示已找到左边界
                }
            }
            else  // 已经找到左边界，现在查找右边界（下一个分隔符）
            {
                findFlag = 2;  // 设置标志，表示已找到右边界
                break;         // 结束循环
            }
        }
    }  
   
    // 处理找到的分段
    if(0 != findFlag && startIndex < strLen - 1)
    {
        // 计算分段长度（右边界位置 - 左边界位置 - 1）
        ret = i - startIndex - 1;
        
        // 检查长度是否超出缓冲区或字符串范围
        if(ret > maxLen || ret > strLen)
        {
            ret = 0;  // 长度超出限制
        }
        else if(ret > 0)
        {
            // 复制分段内容到结果缓冲区（从左边界+1开始）
            strncpy(result, &str[startIndex + 1], ret);
            ret = strlen(result);  // 返回实际复制的内容长度
        }
    }
    
    return ret;  // 返回结果长度或错误码
}



void POWER_control(GPIO_TypeDef *GPIOx ,uint16_t PIN_NUM,int State)
{
	if(State == 1)
	{
		//printf("ON\r\n");
		HAL_GPIO_WritePin(GPIOx,PIN_NUM,GPIO_PIN_SET);
	}
	else if(State == 0)
	{
		//printf("OFF\r\n");
		HAL_GPIO_WritePin(GPIOx,PIN_NUM,GPIO_PIN_RESET);
	}	
}

// 全局变量保存上一次的setting值
static uint16_t last_setting = 0x0000; // 初始化为不可能的值
// 自定义字符检查函数
int isDigit(char c) {
    return (c >= '0' && c <= '9');
}

int isHexDigit(char c) {
    return (c >= '0' && c <= '9') || 
           (c >= 'a' && c <= 'f') || 
           (c >= 'A' && c <= 'F');
}

// 检查字符串是否为数字（十进制或十六进制）
int isNumericString(const char* str) {
    if (str == NULL || *str == '\0') {
        return 0;
    }
    
    // 检查十六进制格式
    if (str[0] == '0' && (str[1] == 'x' || str[1] == 'X')) {
        // 检查十六进制数字
        for (int i = 2; str[i] != '\0'; i++) {
            if (!isHexDigit(str[i])) {
                return 0;
            }
        }
        return 1;
    }
    
    // 检查十进制数字
    for (int i = 0; str[i] != '\0'; i++) {
        if (!isDigit(str[i])) {
            return 0;
        }
    }
    return 1;
}

// 去除字符串末尾的空白字符（换行符、空格等）
void trimWhitespace(char* str) {
    if (str == NULL) return;
    
    int len = strlen(str);
    while (len > 0 && (str[len-1] == '\n' || str[len-1] == '\r' || str[len-1] == ' ' || str[len-1] == '\t')) {
        str[len-1] = '\0';
        len--;
    }
}

// 根据reg.bits设置所有GPIO状态
void applyTrimSettings(TrimRegister16 reg) {
    // BG_VDD_Pin - 通常总是使能，或者根据需要控制
    POWER_control(GPIOB, BG_VDD_Pin, 1); // 总是使能BG_VDD
    
    // BG_IN0 组 (对应 R3_INx, Bits 0-3)
    POWER_control(GPIOB, BG_IN0_0_Pin, reg.bits.R3_IN0);
    POWER_control(GPIOB, BG_IN0_1_Pin, reg.bits.R3_IN1);
    POWER_control(GPIOB, BG_IN0_2_Pin, reg.bits.R3_IN2);
    POWER_control(GPIOB, BG_IN0_3_Pin, reg.bits.R3_IN3);
    
    // BG_IN1 组 (对应 R2_INx, Bits 4-7)
    POWER_control(GPIOB, BG_IN1_0_Pin, reg.bits.R2_IN0);
    POWER_control(GPIOA, BG_IN1_1_Pin, reg.bits.R2_IN1);
    POWER_control(GPIOA, BG_IN1_2_Pin, reg.bits.R2_IN2);
    POWER_control(GPIOB, BG_IN1_3_Pin, reg.bits.R2_IN3);
    
    // BG_IN2 组 (对应 R1_INx, Bits 8-11)
    POWER_control(GPIOA, BG_IN2_0_Pin, reg.bits.R1_IN0);
    POWER_control(GPIOA, BG_IN2_1_Pin, reg.bits.R1_IN1);
    POWER_control(GPIOA, BG_IN2_2_Pin, reg.bits.R1_IN2);
    POWER_control(GPIOA, BG_IN2_3_Pin, reg.bits.R1_IN3);
    
    // LDO 组 (Bits 12-15)
    POWER_control(GPIOA, LDO_0_Pin, reg.bits.LDO0);
    POWER_control(GPIOC, LDO_1_Pin, reg.bits.LDO1);
    POWER_control(GPIOC, LDO_2_Pin, reg.bits.LDO2);
    POWER_control(GPIOA, LDO_3_Pin, reg.bits.LDO3);
}

void processTrimSetting(const char* mode, const char* setting_str) {
    // 创建setting_str的副本并去除空白字符
    char clean_setting[20];
    strncpy(clean_setting, setting_str, sizeof(clean_setting) - 1);
    clean_setting[sizeof(clean_setting) - 1] = '\0';
    trimWhitespace(clean_setting);
    
    // 检查是否为有效的数字字符串
    if (!isNumericString(clean_setting)) {
        printf("Error: Invalid numeric string '%s'\n", clean_setting);
        return;
    }
    
    // 使用strtoul转换字符串为数值
    char* endptr;
    unsigned long value = strtoul(clean_setting, &endptr, 0); // 自动检测进制
    
    // 检查转换错误
    if (endptr == clean_setting || *endptr != '\0') {
        printf("Error: Invalid number format '%s'\n", clean_setting);
        return;
    }
    
    // 检查范围（0-65535）
    if (value > 0xFFFF) {
        printf("Error: Value out of range (0-65535): %s\n", clean_setting);
        return;
    }
    
    uint16_t setting = (uint16_t)value;
    
    // 检查setting是否变化
    if (setting == last_setting) {
        return;
    }
    
    // 更新上一次的值
    last_setting = setting;
    
    // 创建TrimRegister并设置值
    TrimRegister16 reg;
    reg.value = setting;
    
		// 应用硬件设置
    applyTrimSettings(reg);
		
    // 打印结果
		#if defined(DEBUG)
			printf("\n=== New Setting Received ===\n");
			printf("Mode: %s\n", mode);
			printf("Setting string: '%s'\n", clean_setting);
			printf("16-bit value: %u (0x%04X)\n", reg.value, reg.value);
			printf("Binary: ");
			
			// 打印二进制表示（从最高位到最低位，16位）
			for (int i = 15; i >= 0; i--) {
					printf("%d", (reg.value >> i) & 1);
					if (i % 4 == 0 && i != 0) printf(" ");
			}
			printf("\n\n");
			
			// 使用位域访问每一位
			printf("Bit Allocation:\n");
			printf("LDO3   (Bit 15): %d\n", reg.bits.LDO3);
			printf("LDO2   (Bit 14): %d\n", reg.bits.LDO2);
			printf("LDO1   (Bit 13): %d\n", reg.bits.LDO1);
			printf("LDO0   (Bit 12): %d\n", reg.bits.LDO0);
			printf("R1_IN3 (Bit 11): %d\n", reg.bits.R1_IN3);
			printf("R1_IN2 (Bit 10): %d\n", reg.bits.R1_IN2);
			printf("R1_IN1 (Bit 9):  %d\n", reg.bits.R1_IN1);
			printf("R1_IN0 (Bit 8):  %d\n", reg.bits.R1_IN0);
			printf("R2_IN3 (Bit 7):  %d\n", reg.bits.R2_IN3);
			printf("R2_IN2 (Bit 6):  %d\n", reg.bits.R2_IN2);
			printf("R2_IN1 (Bit 5):  %d\n", reg.bits.R2_IN1);
			printf("R2_IN0 (Bit 4):  %d\n", reg.bits.R2_IN0);
			printf("R3_IN3 (Bit 3):  %d\n", reg.bits.R3_IN3);
			printf("R3_IN2 (Bit 2):  %d\n", reg.bits.R3_IN2);
			printf("R3_IN1 (Bit 1):  %d\n", reg.bits.R3_IN1);
			printf("R3_IN0 (Bit 0):  %d\n", reg.bits.R3_IN0);
			printf("================================\n");
		#endif
}




/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{
  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_USART1_UART_Init();
  MX_TIM1_Init();
  /* USER CODE BEGIN 2 */
	HAL_TIM_Base_Start_IT(&htim1);
	UART_Start_Receive_IT(&huart1,(uint8_t *)&aRxBuffer,1);
	printf("Start Up\r\n");
	printf("20250915 Version\r\n");

	




  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */

		
		if(strstr(mode,"Trim")!=NULL)// judge if Trim
	 /**
	 * @brief 判断是否mode是Trim
	 * @param setting 输入字符串,可以是0-65535十进制，也可以是0x0000-0xFFFF二进制
	 * @example Trim:0\n
							Trim:4095\r\n
							Trim:0x1234
							Trim:65535\t
							Trim:0x00FF\n
							Trim:0\n
	 */
 
		{
			processTrimSetting(mode, setting);

		}

		HAL_Delay(1000);

  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL9;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }
  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief TIM1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_TIM1_Init(void)
{

  /* USER CODE BEGIN TIM1_Init 0 */

  /* USER CODE END TIM1_Init 0 */

  TIM_ClockConfigTypeDef sClockSourceConfig = {0};
  TIM_MasterConfigTypeDef sMasterConfig = {0};

  /* USER CODE BEGIN TIM1_Init 1 */

  /* USER CODE END TIM1_Init 1 */
  htim1.Instance = TIM1;
  htim1.Init.Prescaler = 36000-1;
  htim1.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim1.Init.Period = 2000-1;
  htim1.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim1.Init.RepetitionCounter = 0;
  htim1.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
  if (HAL_TIM_Base_Init(&htim1) != HAL_OK)
  {
    Error_Handler();
  }
  sClockSourceConfig.ClockSource = TIM_CLOCKSOURCE_INTERNAL;
  if (HAL_TIM_ConfigClockSource(&htim1, &sClockSourceConfig) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim1, &sMasterConfig) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN TIM1_Init 2 */

  /* USER CODE END TIM1_Init 2 */

}

/**
  * @brief USART1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART1_UART_Init(void)
{

  /* USER CODE BEGIN USART1_Init 0 */

  /* USER CODE END USART1_Init 0 */

  /* USER CODE BEGIN USART1_Init 1 */

  /* USER CODE END USART1_Init 1 */
  huart1.Instance = USART1;
  huart1.Init.BaudRate = 115200;
  huart1.Init.WordLength = UART_WORDLENGTH_8B;
  huart1.Init.StopBits = UART_STOPBITS_1;
  huart1.Init.Parity = UART_PARITY_NONE;
  huart1.Init.Mode = UART_MODE_TX_RX;
  huart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart1.Init.OverSampling = UART_OVERSAMPLING_16;
  if (HAL_UART_Init(&huart1) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USART1_Init 2 */

  /* USER CODE END USART1_Init 2 */

}

/**
  * @brief GPIO Initialization Function
  * @param None
  * @retval None
  */
static void MX_GPIO_Init(void)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOC_CLK_ENABLE();
  __HAL_RCC_GPIOD_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOC, GPIO_PIN_13|LDO_2_Pin|LDO_1_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOA, LDO_0_Pin|LDO_3_Pin|BG_IN2_2_Pin|BG_IN2_1_Pin
                          |BG_IN2_0_Pin|BG_IN2_3_Pin|BG_IN1_2_Pin|BG_IN1_1_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOB, BG_IN1_0_Pin|BG_IN1_3_Pin|BG_IN0_2_Pin|BG_IN0_1_Pin
                          |BG_IN0_0_Pin|BG_IN0_3_Pin|BG_VDD_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pins : PC13 LDO_2_Pin LDO_1_Pin */
  GPIO_InitStruct.Pin = GPIO_PIN_13|LDO_2_Pin|LDO_1_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);

  /*Configure GPIO pins : LDO_0_Pin LDO_3_Pin BG_IN2_2_Pin BG_IN2_1_Pin
                           BG_IN2_0_Pin BG_IN2_3_Pin BG_IN1_2_Pin BG_IN1_1_Pin */
  GPIO_InitStruct.Pin = LDO_0_Pin|LDO_3_Pin|BG_IN2_2_Pin|BG_IN2_1_Pin
                          |BG_IN2_0_Pin|BG_IN2_3_Pin|BG_IN1_2_Pin|BG_IN1_1_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  /*Configure GPIO pins : BG_IN1_0_Pin BG_IN1_3_Pin BG_IN0_2_Pin BG_IN0_1_Pin
                           BG_IN0_0_Pin BG_IN0_3_Pin BG_VDD_Pin */
  GPIO_InitStruct.Pin = BG_IN1_0_Pin|BG_IN1_3_Pin|BG_IN0_2_Pin|BG_IN0_1_Pin
                          |BG_IN0_0_Pin|BG_IN0_3_Pin|BG_VDD_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

}

/* USER CODE BEGIN 4 */

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
	UNUSED(huart);
	if(huart->Instance == USART1)
	{
		
		rec_buffer[Uart1_Rx_Cnt++] = aRxBuffer; 
		if((rec_buffer[Uart1_Rx_Cnt-1] == 0x0A)&&(rec_buffer[Uart1_Rx_Cnt-2] == 0x0D)) //
		{
			Uart1_Rx_Cnt = 0;
			memset(mode,0x00,sizeof(mode));
			memset(setting,0x00,sizeof(setting));
			split(rec_buffer, sizeof(rec_buffer), ":", 1, mode, 16);
			

			split(rec_buffer, sizeof(rec_buffer), ":", 2, setting, 32);
			
			#if defined(DEBUG)
				printf("mode:%s\r\n",mode);
				printf("setting:%s\r\n",setting);
			#endif
				


			memset(rec_buffer,0x00,sizeof(rec_buffer)); 

			}
		}
		HAL_UART_Receive_IT(&huart1, (uint8_t *)&aRxBuffer, 1);   
	
}

void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim){

    

    if (htim->Instance == TIM1){


    }

}

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}

#ifdef  USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */

