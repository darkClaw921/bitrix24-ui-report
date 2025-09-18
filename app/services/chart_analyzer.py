"""Chart analyzer service for automatic chart detection and generation."""

import re
import json
from typing import Dict, Any, Optional, List, Tuple
from langchain.schema import HumanMessage, SystemMessage
from app.services.llm_manager import llm_manager
from app.schemas.chat import ChartData, ChartType


class ChartAnalyzer:
    """Service for analyzing messages and generating charts automatically."""
    
    # Keywords that indicate chart requests in Russian and English
    CHART_KEYWORDS = [
        # Russian keywords
        "график", "диаграмма", "чарт", "визуализация", "построй", "нарисуй", 
        "отобрази", "покажи график", "создай диаграмму", "визуализируй",
        "столбчатая диаграмма", "круговая диаграмма", "линейный график",
        "гистограмма", "scatter plot", "точечная диаграмма",
        
        # English keywords
        "chart", "graph", "plot", "visualization", "visualize", "draw",
        "show chart", "create graph", "display chart", "bar chart",
        "pie chart", "line chart", "scatter plot", "histogram", "area chart"
    ]
    
    # Data patterns that might indicate chartable content
    DATA_PATTERNS = [
        r'\d+\s*[%]',  # Percentages
        r'\d+\s*млн',  # Millions (Russian)
        r'\d+\s*тыс',  # Thousands (Russian)
        r'\d+\s*million',  # Millions (English)
        r'\d+\s*thousand',  # Thousands (English)
        r'\d+\.\d+',   # Decimal numbers
        r'\b\d{4}\b',  # Years
        r'(?:янв|фев|мар|апр|май|июн|июл|авг|сен|окт|ноя|дек)',  # Russian months
        r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)',  # English months
    ]
    
    def __init__(self):
        """Initialize chart analyzer."""
        self.chart_generation_prompt = self._create_chart_prompt_template()
    
    def detect_chart_request(self, message: str) -> bool:
        """Detect if message contains a chart request."""
        message_lower = message.lower()
        
        # Check for explicit chart keywords
        for keyword in self.CHART_KEYWORDS:
            if keyword in message_lower:
                return True
        
        # Check for data patterns combined with visualization words
        visualization_words = ["покажи", "отобрази", "визуализируй", "show", "display", "visualize"]
        has_data = any(re.search(pattern, message) for pattern in self.DATA_PATTERNS)
        has_visualization_word = any(word in message_lower for word in visualization_words)
        
        return has_data and has_visualization_word
    
    def extract_chart_requirements(self, message: str) -> Dict[str, Any]:
        """Extract chart requirements from message."""
        message_lower = message.lower()
        
        # Determine chart type based on keywords
        chart_type = self._determine_chart_type(message_lower)
        
        # Extract potential data points
        numbers = re.findall(r'\b\d+(?:\.\d+)?\b', message)
        percentages = re.findall(r'\d+\s*[%]', message)
        
        # Extract potential labels
        months_ru = re.findall(r'(?:январь|февраль|март|апрель|май|июнь|июль|август|сентябрь|октябрь|ноябрь|декабрь)', message, re.IGNORECASE)
        months_en = re.findall(r'(?:january|february|march|april|may|june|july|august|september|october|november|december)', message, re.IGNORECASE)
        
        return {
            "chart_type": chart_type,
            "has_numbers": bool(numbers),
            "has_percentages": bool(percentages),
            "numbers": numbers[:10],  # Limit to first 10 numbers
            "percentages": percentages[:10],
            "months": months_ru + months_en,
            "original_message": message
        }
    
    def _determine_chart_type(self, message_lower: str) -> str:
        """Determine the most appropriate chart type based on message content."""
        # Pie chart indicators
        pie_indicators = ["круговая", "pie", "доля", "процент", "распределение", "share", "proportion"]
        if any(indicator in message_lower for indicator in pie_indicators):
            return "pie"
        
        # Bar chart indicators
        bar_indicators = ["столбчатая", "bar", "сравнение", "comparison", "compare"]
        if any(indicator in message_lower for indicator in bar_indicators):
            return "bar"
        
        # Line chart indicators
        line_indicators = ["линейный", "line", "тренд", "trend", "динамика", "dynamics", "изменение", "change"]
        if any(indicator in message_lower for indicator in line_indicators):
            return "line"
        
        # Scatter plot indicators
        scatter_indicators = ["scatter", "точечная", "корреляция", "correlation", "зависимость", "relationship"]
        if any(indicator in message_lower for indicator in scatter_indicators):
            return "scatter"
        
        # Default to line chart
        return "line"
    
    def _create_chart_prompt_template(self) -> str:
        """Create prompt template for chart generation."""
        return """Вы помощник по созданию графиков. Пользователь запросил создание графика. 

Проанализируйте следующее сообщение и создайте JSON-конфигурацию для графика с использованием Chart.js.

Требования:
1. Определите тип графика (line, bar, pie, scatter, area)
2. Извлеките или создайте разумные данные на основе контекста
3. Создайте подходящие метки и значения
4. Добавьте заголовок и подписи осей

Сообщение пользователя: {user_message}

Дополнительная информация:
- Предполагаемый тип графика: {chart_type}
- Найденные числа: {numbers}
- Найденные проценты: {percentages}
- Найденные месяцы: {months}

Ответьте ТОЛЬКО в следующем JSON формате (без дополнительного текста):
{{
    "type": "line|bar|pie|scatter|area",
    "data": {{
        "labels": ["Метка1", "Метка2", ...],
        "datasets": [{{
            "label": "Название набора данных",
            "data": [число1, число2, ...],
            "backgroundColor": ["#3b82f6", "#60a5fa", "#93c5fd", ...],
            "borderColor": "#2563eb",
            "borderWidth": 2
        }}]
    }},
    "options": {{
        "responsive": true,
        "plugins": {{
            "title": {{
                "display": true,
                "text": "Заголовок графика"
            }},
            "legend": {{
                "display": true,
                "position": "top"
            }}
        }},
        "scales": {{
            "y": {{
                "beginAtZero": true,
                "title": {{
                    "display": true,
                    "text": "Y-ось"
                }}
            }},
            "x": {{
                "title": {{
                    "display": true,
                    "text": "X-ось"
                }}
            }}
        }}
    }},
    "title": "Краткий заголовок графика"
}}

Если данных недостаточно, создайте пример данных, соответствующих контексту запроса."""
    
    async def generate_chart_data(
        self,
        user_message: str,
        chart_requirements: Dict[str, Any],
        provider_name: str = "openai"
    ) -> Optional[ChartData]:
        """Generate chart data using LLM."""
        try:
            # Create chart generation prompt
            prompt = self.chart_generation_prompt.format(
                user_message=user_message,
                chart_type=chart_requirements.get("chart_type", "line"),
                numbers=chart_requirements.get("numbers", []),
                percentages=chart_requirements.get("percentages", []),
                months=chart_requirements.get("months", [])
            )
            
            # Create messages for LLM
            messages = [
                SystemMessage(content="Вы эксперт по созданию графиков и визуализации данных."),
                HumanMessage(content=prompt)
            ]
            
            # Generate response using LLM
            response = await llm_manager.generate_response(
                messages=messages,
                provider_name=provider_name,
                temperature=0.3,  # Lower temperature for more consistent JSON output
                max_tokens=1000
            )
            
            # Parse JSON response
            chart_config = self._parse_chart_response(response)
            if chart_config:
                return ChartData(**chart_config)
            
        except Exception as e:
            print(f"Error generating chart data: {e}")
        
        return None
    
    def _parse_chart_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse LLM response to extract chart configuration."""
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                chart_config = json.loads(json_str)
                
                # Validate required fields
                if self._validate_chart_config(chart_config):
                    return chart_config
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
        except Exception as e:
            print(f"Error parsing chart response: {e}")
        
        return None
    
    def _validate_chart_config(self, config: Dict[str, Any]) -> bool:
        """Validate chart configuration."""
        required_fields = ["type", "data", "options"]
        
        # Check required top-level fields
        if not all(field in config for field in required_fields):
            return False
        
        # Check chart type
        valid_types = ["line", "bar", "pie", "scatter", "area"]
        if config["type"] not in valid_types:
            return False
        
        # Check data structure
        data = config.get("data", {})
        if not isinstance(data, dict):
            return False
        
        if "labels" not in data or "datasets" not in data:
            return False
        
        # Check datasets
        datasets = data.get("datasets", [])
        if not isinstance(datasets, list) or not datasets:
            return False
        
        for dataset in datasets:
            if not isinstance(dataset, dict) or "data" not in dataset:
                return False
        
        return True
    
    def create_fallback_chart(self, message: str, chart_type: str = "line") -> ChartData:
        """Create a fallback chart when LLM generation fails."""
        fallback_data = {
            "type": chart_type,
            "data": {
                "labels": ["Пример 1", "Пример 2", "Пример 3", "Пример 4"],
                "datasets": [{
                    "label": "Данные",
                    "data": [10, 20, 15, 25],
                    "backgroundColor": ["#3b82f6", "#60a5fa", "#93c5fd", "#dbeafe"],
                    "borderColor": "#2563eb",
                    "borderWidth": 2
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {
                        "display": True,
                        "text": "Пример графика"
                    }
                }
            },
            "title": "Пример графика"
        }
        
        return ChartData(**fallback_data)


# Global chart analyzer instance
chart_analyzer = ChartAnalyzer()