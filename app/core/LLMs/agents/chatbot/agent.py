from typing import Optional
from typing_extensions import TypedDict
from typing import Annotated
from pydantic import BaseModel

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from app.core.config import settings
from app.schemas.message import MessageCreate as Message

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

class LangGraphAgent:
    def __init__(self, response_schema: type[BaseModel] | None = None):
        self.llm = ChatGoogleGenerativeAI(
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_output_tokens=settings.LLM_MAX_TOKENS,
            api_key=settings.GEMINI_API_KEY,
        )

        def call_model(state: AgentState):
            response = self.llm.invoke(state["messages"])
            return {"messages": [response]}

        workflow = StateGraph(AgentState)
        workflow.add_node("agent", call_model)
        workflow.add_edge(START, "agent")
        workflow.add_edge("agent", END)

        self.app = workflow.compile()

    def _to_lc_messages(self, messages: list[Message], context: str = "") -> list[BaseMessage]:
        sensor_section = f"\n\n{context}" if context else ""
        lc_messages: list[BaseMessage] = [
            SystemMessage(content=(
                "Você é o assistente virtual do 'Sistema Inteligente de Monitoramento Agrícola para Otimização da Agricultura de Precisão em Propriedades Rurais Utilizando IoT'. "
                "Sua especialidade é gerar relatórios detalhados das plantações, interpretar dados recebidos de sensores no campo (como umidade do solo, temperatura, pH, clima) "
                "e fornecer recomendações agronômicas precisas para otimizar a gestão da propriedade rural.\n"
                "Quando o usuário pedir gráficos ou visualizações de dados, gere um bloco de código com linguagem 'chart' contendo JSON no formato:\n"
                "```chart\n"
                "{\"type\":\"line\",\"title\":\"Título\",\"data\":[{\"time\":\"HH:MM\",\"valor\":0.0}],\"xKey\":\"time\","
                "\"series\":[{\"key\":\"valor\",\"name\":\"Nome\",\"color\":\"#32A041\"}]}\n"
                "```\n"
                "Tipos suportados: line, bar, area. Use os dados reais dos sensores disponíveis no contexto."
                + sensor_section
            ))
        ]
        for msg in messages:
            if msg.role == "user":
                lc_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                lc_messages.append(AIMessage(content=msg.content))
        return lc_messages

    async def get_response(
        self,
        messages: list[Message],
        session_id: str,
        user_id: Optional[str] = None,
        context: str = "",
    ) -> dict:
        try:
            lc_messages = self._to_lc_messages(messages, context)
            result = await self.app.ainvoke(
                {"messages": lc_messages},
                config={"configurable": {"thread_id": session_id}}
            )
            final_message = result["messages"][-1]
            return {"response": final_message.content}
        except Exception as e:
            return {"response": f"Erro interno do agente: {str(e)}"}