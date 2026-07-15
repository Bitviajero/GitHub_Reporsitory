from qwen_agent.agents import Assistant

# Configuración para Ollama local en Windows
llm_cfg = {
    "model": "qwen3:8b",
    "model_server": "http://localhost:11434/v1",
    "api_key": "EMPTY"
}

# Crear agente básico (sin sandbox de código para simplificar en Windows)
bot = Assistant(llm=llm_cfg)

# Ejecutar tarea
mensaje = {"role": "user", "content": "Escribe un script en Python que liste los archivos .pdf de C:\\Users\\%USERNAME%\\Downloads"}
for respuesta in bot.run(messages=[mensaje]):
    print(respuesta)