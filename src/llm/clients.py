from src.llm import openai_client


def history_content(item):
    if isinstance(item, dict):
        return item.get("content", "")
    return getattr(item, "content", str(item))


class OpenAICompatibleClient:
    def __init__(self, key, url, model_fullname, retry_sleep=1):
        self.key = key
        self.url = url
        self.model_fullname = model_fullname
        self.retry_sleep = retry_sleep

    def call_with_message(self, messages):
        return openai_client.call_with_message(self.key, self.url, self.model_fullname, messages)

    def call_with_3messages(self, messages):
        return openai_client.call_with_3messages(self.key, self.url, self.model_fullname, messages)

    def call_with_2messages(self, messages):
        return openai_client.call_with_2messages(self.key, self.url, self.model_fullname, messages)

    def is_valid(self, response):
        return bool(response and response.choices and len(response.choices) > 0 and response.choices[0].message)

    def get_content(self, response):
        return response.choices[0].message.content


class DashscopeClient:
    def __init__(self, key, model_fullname, retry_sleep=3):
        self.key = key
        self.model_fullname = model_fullname
        self.retry_sleep = retry_sleep

    def _call(self, messages):
        from http import HTTPStatus
        import dashscope

        response = dashscope.Generation.call(
            api_key=self.key,
            model=self.model_fullname,
            messages=messages,
            result_format="message",
        )
        if response.status_code == HTTPStatus.OK:
            return response
        print(
            "Request id: %s, Status code: %s, error code: %s, error message: %s"
            % (response.request_id, response.status_code, response.code, response.message)
        )
        return None

    def call_with_message(self, messages):
        return self._call(messages)

    def call_with_3messages(self, messages):
        import time

        history_response = []
        messages = [msg for sublist in messages for msg in sublist]
        message_with_historys = []
        print("Processing multiple rounds of messages")
        response = None
        for message in messages:
            message_with_historys.append(message)
            success = False
            while not success:
                response = self._call(message_with_historys)
                if response is None:
                    print("retry in 3sec")
                    time.sleep(3)
                else:
                    generated_message = response["output"]["choices"][0]["message"]
                    message_with_historys.append(generated_message)
                    history_response.append(generated_message)
                    success = True
        return response, history_response

    def call_with_2messages(self, messages):
        import time

        history_response = []
        messages = [msg for sublist in messages for msg in sublist]
        message_with_historys = []
        print("Processing multiple rounds of 3messages")
        count = 0
        response = None
        for message in messages:
            if count == 0:
                message_with_historys.append(message)
                count += 1
                continue
            message_with_historys.append(message)
            success = False
            while not success:
                response = self._call(message_with_historys)
                if response is None:
                    print("retry in 3sec")
                    time.sleep(3)
                else:
                    generated_message = response["output"]["choices"][0]["message"]
                    message_with_historys.append(generated_message)
                    history_response.append(generated_message)
                    success = True
            count += 1
        return response, history_response

    def is_valid(self, response):
        return response is not None

    def get_content(self, response):
        return response["output"]["choices"][0]["message"]["content"]


class OllamaClient:
    def __init__(self, model_fullname, retry_sleep=1):
        self.model_fullname = model_fullname
        self.retry_sleep = retry_sleep

    def call_with_message(self, messages):
        from src.ollama import ollama_client

        return ollama_client.call_with_message(self.model_fullname, messages)

    def call_with_3messages(self, messages):
        from src.ollama import ollama_client

        return ollama_client.call_with_3messages(self.model_fullname, messages)

    def call_with_2messages(self, messages):
        from src.ollama import ollama_client

        return ollama_client.call_with_2messages(self.model_fullname, messages)

    def is_valid(self, response):
        if response is None:
            return False
        if hasattr(response, "choices"):
            return bool(response.choices and len(response.choices) > 0 and response.choices[0].message)
        return bool(response.get("message"))

    def get_content(self, response):
        if hasattr(response, "choices"):
            return response.choices[0].message.content
        return response["message"]["content"]


def build_client(provider, key, url, model_fullname, retry_sleep=None):
    from src.config import PROVIDERS

    spec = PROVIDERS[provider]
    kind = spec["client"]
    retry_sleep = spec["retry_sleep"] if retry_sleep is None else retry_sleep
    if kind == "openai":
        return OpenAICompatibleClient(key, url, model_fullname, retry_sleep=retry_sleep)
    if kind == "dashscope":
        return DashscopeClient(key, model_fullname, retry_sleep=retry_sleep)
    if kind == "ollama":
        return OllamaClient(model_fullname, retry_sleep=retry_sleep)
    raise ValueError(f"unknown client kind: {kind}")
