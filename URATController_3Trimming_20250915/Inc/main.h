/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.h
  * @brief          : Header for main.c file.
  *                   This file contains the common defines of the application.
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

/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "stm32f1xx_hal.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Exported types ------------------------------------------------------------*/
/* USER CODE BEGIN ET */

/* USER CODE END ET */

/* Exported constants --------------------------------------------------------*/
/* USER CODE BEGIN EC */

/* USER CODE END EC */

/* Exported macro ------------------------------------------------------------*/
/* USER CODE BEGIN EM */

/* USER CODE END EM */

/* Exported functions prototypes ---------------------------------------------*/
void Error_Handler(void);

/* USER CODE BEGIN EFP */

/* USER CODE END EFP */

/* Private defines -----------------------------------------------------------*/
#define LDO_2_Pin GPIO_PIN_14
#define LDO_2_GPIO_Port GPIOC
#define LDO_1_Pin GPIO_PIN_15
#define LDO_1_GPIO_Port GPIOC
#define LDO_0_Pin GPIO_PIN_0
#define LDO_0_GPIO_Port GPIOA
#define LDO_3_Pin GPIO_PIN_1
#define LDO_3_GPIO_Port GPIOA
#define BG_IN2_2_Pin GPIO_PIN_2
#define BG_IN2_2_GPIO_Port GPIOA
#define BG_IN2_1_Pin GPIO_PIN_3
#define BG_IN2_1_GPIO_Port GPIOA
#define BG_IN2_0_Pin GPIO_PIN_4
#define BG_IN2_0_GPIO_Port GPIOA
#define BG_IN2_3_Pin GPIO_PIN_5
#define BG_IN2_3_GPIO_Port GPIOA
#define BG_IN1_2_Pin GPIO_PIN_6
#define BG_IN1_2_GPIO_Port GPIOA
#define BG_IN1_1_Pin GPIO_PIN_7
#define BG_IN1_1_GPIO_Port GPIOA
#define BG_IN1_0_Pin GPIO_PIN_0
#define BG_IN1_0_GPIO_Port GPIOB
#define BG_IN1_3_Pin GPIO_PIN_3
#define BG_IN1_3_GPIO_Port GPIOB
#define BG_IN0_2_Pin GPIO_PIN_4
#define BG_IN0_2_GPIO_Port GPIOB
#define BG_IN0_1_Pin GPIO_PIN_5
#define BG_IN0_1_GPIO_Port GPIOB
#define BG_IN0_0_Pin GPIO_PIN_6
#define BG_IN0_0_GPIO_Port GPIOB
#define BG_IN0_3_Pin GPIO_PIN_7
#define BG_IN0_3_GPIO_Port GPIOB
#define BG_VDD_Pin GPIO_PIN_8
#define BG_VDD_GPIO_Port GPIOB
/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
