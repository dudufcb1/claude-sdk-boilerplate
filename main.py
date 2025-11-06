from claude_config import get_anthropic_client, get_model


def main():
    client = get_anthropic_client()
    model = get_model()

    print(f"Usando modelo: {model}")
    print("Chat iniciado. Escribe 'salir' para terminar.\n")

    messages = []

    while True:
        user_input = input("Tú: ")

        if user_input.lower() in ['salir', 'exit', 'quit']:
            print("Adiós!")
            break

        messages.append({"role": "user", "content": user_input})

        response = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=messages
        )

        assistant_message = response.content[0].text
        messages.append({"role": "assistant", "content": assistant_message})

        print(f"Claude: {assistant_message}\n")


if __name__ == "__main__":
    main()

