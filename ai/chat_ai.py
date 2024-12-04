import json
import os

from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from entity.moment_info import MomentInfo


class BaseGenerateAi:
    def __init__(self):
        api_key = os.getenv("MODEL_API_KEY")
        base_url = os.getenv("MODEL_BASE_URL")
        model = os.getenv("MODEL")
        self.model = ChatOpenAI(openai_api_key=api_key, openai_api_base=base_url,   model_name=model)


    def generate_moment_conclusion(self, moments:list[MomentInfo]):
        """
        生成朋友圈总结
        :param prompt: 提示词
        :return:总结
        """
        response_schemas = [
            ResponseSchema(name="总结", description="根据时间线对当前用户一天内整体活动的总结，尽量全面一点"),
            ResponseSchema(name="重点", description="提取当前用户最重要的活动"),
            ResponseSchema(name="心情", description="根据全部信息猜测用户的心情状态"),
            ResponseSchema(name="赋诗", description="用一首五言绝句总结当前用户的一天")
        ]
        output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
        format_instructions = output_parser.get_format_instructions()
        # print(format_instructions)
        # 加入至template中
        template = """
        以下是当前用户在朋友圈内发出的一天内的所有活动，请分析并总结，提取重要信息
        {format_instructions}
        # 输入如下:
        {input}
        回答的时候尽量活泼一点
        """
        prompt_template = PromptTemplate(
            input_variables=["input"],
            partial_variables={"format_instructions": format_instructions},
            template=template
        )
        chain = prompt_template | self.model | output_parser
        prompt = ""
        for event in moments:
            prompt += f"{json.dumps(event.to_dict())}\n"
        return chain.invoke(prompt)