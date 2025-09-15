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


//�����Ҫ����print����ȡ��DEBUGע��
#define DEBUG 
	
char rec_buffer[RXBUFFERSIZE];   
char mode[128];
char setting[1024];



uint8_t Uart1_Rx_Cnt = 0;		
uint8_t aRxBuffer;	



// ����16λλ��ṹ��
typedef struct {
    unsigned int R3_IN0 : 1;  // ���λ (Bit 0)
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
    unsigned int LDO3  : 1;   // ���λ (Bit 15)
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
 * @brief �ָ��ַ�������
 * @param str �����ַ���
 * @param strLen �����ַ�������
 * @param splitChar �ָ����ַ���
 * @param index Ҫ��ȡ�ķֶ���������1��ʼ��
 * @param result �洢����Ļ�����
 * @param maxLen �������������󳤶�
 * @return �ɹ����طֶγ��ȣ�ʧ�ܷ��ش�����
 */
int split(const char* str, int strLen, const char* splitChar, int index, char* result, int maxLen)
{
    int i = 0;              // ѭ������
    int ret = 0;            // ����ֵ
    int findLen = 0;        // �������ĳ���
    int findFlag = 0;       // ����״̬��־
    int startIndex = 0;     // �ֶ���ʼλ��
    int splitCharLen = 0;   // �ָ�������

    // ������飺�����ַ�����������������ָ�������Ϊ�գ������������0
    if(NULL == str || NULL == result || NULL == splitChar || index <= 0)
    {
        return -1;  // ��������
    }      
    
    // ��ȡ�ָ�������
    splitCharLen = strlen(splitChar);
    
    // ����������ĳ��ȣ��ܳ��ȼ�ȥ�ָ������ȣ�
    findLen = strLen - splitCharLen;
    if(findLen < 0)
    {
        return -2;  // �ַ������Ȳ���
    }  
   
    // �����ַ������ҷָ���
    for(; i <= findLen && str[i] != '\0'; i++)
    {
        // ��鵱ǰλ���Ƿ�ƥ��ָ���
        if(strncmp(&str[i], splitChar, splitCharLen) == 0)
        {
            if(0 == findFlag)  // ��һ���ҵ��ָ�����������߽磩
            {
                startIndex++;  // �ָ�����������
                
                if(1 == index)  // ����ǵ�һ���ֶ�
                {
                    // ���ƴӿ�ʼ����ǰ�ָ���֮ǰ������
                    strncpy(result, &str[0], i);
                    ret = i;    // ���طֶγ���
                    break;      // ����ѭ��
                }
                else if(startIndex + 1 == index)  // �ҵ�Ŀ��ֶε�ǰһ���ָ���
                {
                    startIndex = i;  // ��¼�ֶ���ʼλ�ã���ǰ�ָ���λ�ã�
                    findFlag = 1;    // ���ñ�־����ʾ���ҵ���߽�
                }
            }
            else  // �Ѿ��ҵ���߽磬���ڲ����ұ߽磨��һ���ָ�����
            {
                findFlag = 2;  // ���ñ�־����ʾ���ҵ��ұ߽�
                break;         // ����ѭ��
            }
        }
    }  
   
    // �����ҵ��ķֶ�
    if(0 != findFlag && startIndex < strLen - 1)
    {
        // ����ֶγ��ȣ��ұ߽�λ�� - ��߽�λ�� - 1��
        ret = i - startIndex - 1;
        
        // ��鳤���Ƿ񳬳����������ַ�����Χ
        if(ret > maxLen || ret > strLen)
        {
            ret = 0;  // ���ȳ�������
        }
        else if(ret > 0)
        {
            // ���Ʒֶ����ݵ����������������߽�+1��ʼ��
            strncpy(result, &str[startIndex + 1], ret);
            ret = strlen(result);  // ����ʵ�ʸ��Ƶ����ݳ���
        }
    }
    
    return ret;  // ���ؽ�����Ȼ������
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

// ȫ�ֱ���������һ�ε�settingֵ
static uint16_t last_setting = 0x0000; // ��ʼ��Ϊ�����ܵ�ֵ
// �Զ����ַ���麯��
int isDigit(char c) {
    return (c >= '0' && c <= '9');
}

int isHexDigit(char c) {
    return (c >= '0' && c <= '9') || 
           (c >= 'a' && c <= 'f') || 
           (c >= 'A' && c <= 'F');
}

// ����ַ����Ƿ�Ϊ���֣�ʮ���ƻ�ʮ�����ƣ�
int isNumericString(const char* str) {
    if (str == NULL || *str == '\0') {
        return 0;
    }
    
    // ���ʮ�����Ƹ�ʽ
    if (str[0] == '0' && (str[1] == 'x' || str[1] == 'X')) {
        // ���ʮ����������
        for (int i = 2; str[i] != '\0'; i++) {
            if (!isHexDigit(str[i])) {
                return 0;
            }
        }
        return 1;
    }
    
    // ���ʮ��������
    for (int i = 0; str[i] != '\0'; i++) {
        if (!isDigit(str[i])) {
            return 0;
        }
    }
    return 1;
}

// ȥ���ַ���ĩβ�Ŀհ��ַ������з����ո�ȣ�
void trimWhitespace(char* str) {
    if (str == NULL) return;
    
    int len = strlen(str);
    while (len > 0 && (str[len-1] == '\n' || str[len-1] == '\r' || str[len-1] == ' ' || str[len-1] == '\t')) {
        str[len-1] = '\0';
        len--;
    }
}

// ����reg.bits��������GPIO״̬
void applyTrimSettings(TrimRegister16 reg) {
    // BG_VDD_Pin - ͨ������ʹ�ܣ����߸�����Ҫ����
    POWER_control(GPIOB, BG_VDD_Pin, 1); // ����ʹ��BG_VDD
    
    // BG_IN0 �� (��Ӧ R3_INx, Bits 0-3)
    POWER_control(GPIOB, BG_IN0_0_Pin, reg.bits.R3_IN0);
    POWER_control(GPIOB, BG_IN0_1_Pin, reg.bits.R3_IN1);
    POWER_control(GPIOB, BG_IN0_2_Pin, reg.bits.R3_IN2);
    POWER_control(GPIOB, BG_IN0_3_Pin, reg.bits.R3_IN3);
    
    // BG_IN1 �� (��Ӧ R2_INx, Bits 4-7)
    POWER_control(GPIOB, BG_IN1_0_Pin, reg.bits.R2_IN0);
    POWER_control(GPIOA, BG_IN1_1_Pin, reg.bits.R2_IN1);
    POWER_control(GPIOA, BG_IN1_2_Pin, reg.bits.R2_IN2);
    POWER_control(GPIOB, BG_IN1_3_Pin, reg.bits.R2_IN3);
    
    // BG_IN2 �� (��Ӧ R1_INx, Bits 8-11)
    POWER_control(GPIOA, BG_IN2_0_Pin, reg.bits.R1_IN0);
    POWER_control(GPIOA, BG_IN2_1_Pin, reg.bits.R1_IN1);
    POWER_control(GPIOA, BG_IN2_2_Pin, reg.bits.R1_IN2);
    POWER_control(GPIOA, BG_IN2_3_Pin, reg.bits.R1_IN3);
    
    // LDO �� (Bits 12-15)
    POWER_control(GPIOA, LDO_0_Pin, reg.bits.LDO0);
    POWER_control(GPIOC, LDO_1_Pin, reg.bits.LDO1);
    POWER_control(GPIOC, LDO_2_Pin, reg.bits.LDO2);
    POWER_control(GPIOA, LDO_3_Pin, reg.bits.LDO3);
}

void processTrimSetting(const char* mode, const char* setting_str) {
    // ����setting_str�ĸ�����ȥ���հ��ַ�
    char clean_setting[20];
    strncpy(clean_setting, setting_str, sizeof(clean_setting) - 1);
    clean_setting[sizeof(clean_setting) - 1] = '\0';
    trimWhitespace(clean_setting);
    
    // ����Ƿ�Ϊ��Ч�������ַ���
    if (!isNumericString(clean_setting)) {
        printf("Error: Invalid numeric string '%s'\n", clean_setting);
        return;
    }
    
    // ʹ��strtoulת���ַ���Ϊ��ֵ
    char* endptr;
    unsigned long value = strtoul(clean_setting, &endptr, 0); // �Զ�������
    
    // ���ת������
    if (endptr == clean_setting || *endptr != '\0') {
        printf("Error: Invalid number format '%s'\n", clean_setting);
        return;
    }
    
    // ��鷶Χ��0-65535��
    if (value > 0xFFFF) {
        printf("Error: Value out of range (0-65535): %s\n", clean_setting);
        return;
    }
    
    uint16_t setting = (uint16_t)value;
    
    // ���setting�Ƿ�仯
    if (setting == last_setting) {
        return;
    }
    
    // ������һ�ε�ֵ
    last_setting = setting;
    
    // ����TrimRegister������ֵ
    TrimRegister16 reg;
    reg.value = setting;
    
		// Ӧ��Ӳ������
    applyTrimSettings(reg);
		
    // ��ӡ���
		#if defined(DEBUG)
			printf("\n=== New Setting Received ===\n");
			printf("Mode: %s\n", mode);
			printf("Setting string: '%s'\n", clean_setting);
			printf("16-bit value: %u (0x%04X)\n", reg.value, reg.value);
			printf("Binary: ");
			
			// ��ӡ�����Ʊ�ʾ�������λ�����λ��16λ��
			for (int i = 15; i >= 0; i--) {
					printf("%d", (reg.value >> i) & 1);
					if (i % 4 == 0 && i != 0) printf(" ");
			}
			printf("\n\n");
			
			// ʹ��λ�����ÿһλ
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
	 * @brief �ж��Ƿ�mode��Trim
	 * @param setting �����ַ���,������0-65535ʮ���ƣ�Ҳ������0x0000-0xFFFF������
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

