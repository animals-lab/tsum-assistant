from inspect import signature
from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo
from typing import Any, Awaitable, Optional, Callable, Type, List, Tuple, Union, cast

from llama_index.core.tools import (
    FunctionTool,
    ToolOutput,
    ToolMetadata,
)
from llama_index.core.workflow import (
    Context,
)

import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from dataclasses import dataclass
from urllib.request import urlopen
import gzip
from io import BytesIO

@dataclass
class TsumProduct:
    id: str
    name: str
    url: str
    price: float
    currency: str
    category: str
    picture: str
    brand: Optional[str] = None
    description: Optional[str] = None
    available: bool = True
    size: Optional[str] = None
    color: Optional[str] = None

class TsumXMLParser:
    def __init__(self, url: str = "https://st.tsum.com/feeds/yandex_smart.xml"):
        self.url = url
    
    def _download_and_decompress(self) -> str:
        """Download and decompress gzipped XML feed."""
        response = urlopen(self.url)
        compressed_data = response.read()
        
        # Decompress gzipped content
        buf = BytesIO(compressed_data)
        with gzip.GzipFile(fileobj=buf) as f:
            return f.read().decode('utf-8')

    def parse(self) -> List[TsumProduct]:
        """Parse the XML feed and return list of products."""
        try:
            xml_content = self._download_and_decompress()
            root = ET.fromstring(xml_content)
            
            # Find all offer elements
            products = []
            namespace = {'yml': 'http://www.w3.org/1999/xhtml'}  # Adjust namespace if needed
            
            for offer in root.findall('.//offer'):
                try:
                    product = TsumProduct(
                        id=offer.get('id'),
                        name=self._get_text(offer, 'name'),
                        url=self._get_text(offer, 'url'),
                        price=float(self._get_text(offer, 'price', '0')),
                        currency=self._get_text(offer, 'currencyId', 'RUB'),
                        category=self._get_text(offer, 'category'),
                        picture=self._get_text(offer, 'picture'),
                        brand=self._get_text(offer, 'vendor'),
                        description=self._get_text(offer, 'description'),
                        available=offer.get('available', 'true').lower() == 'true',
                        size=self._get_param(offer, 'Размер'),
                        color=self._get_param(offer, 'Цвет')
                    )
                    products.append(product)
                except Exception as e:
                    print(f"Error parsing product: {e}")
                    continue
                    
            return products
            
        except Exception as e:
            print(f"Error parsing XML feed: {e}")
            return []

    def _get_text(self, element: ET.Element, tag: str, default: str = '') -> str:
        """Helper method to safely get text content of an XML element."""
        child = element.find(tag)
        return child.text if child is not None and child.text else default

    def _get_param(self, offer: ET.Element, param_name: str) -> Optional[str]:
        """Helper method to get parameter value by name from param elements."""
        for param in offer.findall('param'):
            if param.get('name') == param_name:
                return param.text
        return None

# Example usage
if __name__ == "__main__":
    parser = TsumXMLParser()
    products = parser.parse()
    
    # Print first 5 products as example
    for product in products[:5]:
        print(f"\nProduct: {product.name}")
        print(f"Brand: {product.brand}")
        print(f"Price: {product.price} {product.currency}")
        print(f"Size: {product.size}")
        print(f"Color: {product.color}")
        print(f"URL: {product.url}")
        print("-" * 50)


AsyncCallable = Callable[..., Awaitable[Any]]


def create_schema_from_function(
    name: str,
    func: Union[Callable[..., Any], Callable[..., Awaitable[Any]]],
    additional_fields: Optional[
        List[Union[Tuple[str, Type, Any], Tuple[str, Type]]]
    ] = None,
) -> Type[BaseModel]:
    """Create schema from function."""
    fields = {}
    params = signature(func).parameters
    for param_name in params:
        # TODO: Very hacky way to remove the ctx parameter from the signature
        if param_name == "ctx":
            continue

        param_type = params[param_name].annotation
        param_default = params[param_name].default

        if param_type is params[param_name].empty:
            param_type = Any

        if param_default is params[param_name].empty:
            # Required field
            fields[param_name] = (param_type, FieldInfo())
        elif isinstance(param_default, FieldInfo):
            # Field with pydantic.Field as default value
            fields[param_name] = (param_type, param_default)
        else:
            fields[param_name] = (param_type, FieldInfo(default=param_default))

    additional_fields = additional_fields or []
    for field_info in additional_fields:
        if len(field_info) == 3:
            field_info = cast(Tuple[str, Type, Any], field_info)
            field_name, field_type, field_default = field_info
            fields[field_name] = (field_type, FieldInfo(default=field_default))
        elif len(field_info) == 2:
            # Required field has no default value
            field_info = cast(Tuple[str, Type], field_info)
            field_name, field_type = field_info
            fields[field_name] = (field_type, FieldInfo())
        else:
            raise ValueError(
                f"Invalid additional field info: {field_info}. "
                "Must be a tuple of length 2 or 3."
            )

    return create_model(name, **fields)  # type: ignore


class FunctionToolWithContext(FunctionTool):
    """
    A function tool that also includes passing in workflow context.

    Only overrides the call methods to include the context.
    """

    @classmethod
    def from_defaults(
        cls,
        fn: Optional[Callable[..., Any]] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        return_direct: bool = False,
        fn_schema: Optional[Type[BaseModel]] = None,
        async_fn: Optional[AsyncCallable] = None,
        tool_metadata: Optional[ToolMetadata] = None,
    ) -> "FunctionTool":
        if tool_metadata is None:
            fn_to_parse = fn or async_fn
            assert fn_to_parse is not None, "fn or async_fn must be provided."
            name = name or fn_to_parse.__name__
            docstring = fn_to_parse.__doc__

            # TODO: Very hacky way to remove the ctx parameter from the signature
            signature_str = str(signature(fn_to_parse))
            signature_str = signature_str.replace(
                "ctx: llama_index.core.workflow.context.Context, ", ""
            )
            description = description or f"{name}{signature_str}\n{docstring}"
            if fn_schema is None:
                fn_schema = create_schema_from_function(
                    f"{name}", fn_to_parse, additional_fields=None
                )
            tool_metadata = ToolMetadata(
                name=name,
                description=description,
                fn_schema=fn_schema,
                return_direct=return_direct,
            )
        return cls(fn=fn, metadata=tool_metadata, async_fn=async_fn)

    def call(self, ctx: Context, *args: Any, **kwargs: Any) -> ToolOutput:
        """Call."""
        tool_output = self._fn(ctx, *args, **kwargs)
        return ToolOutput(
            content=str(tool_output),
            tool_name=self.metadata.name,
            raw_input={"args": args, "kwargs": kwargs},
            raw_output=tool_output,
        )

    async def acall(self, ctx: Context, *args: Any, **kwargs: Any) -> ToolOutput:
        """Call."""
        tool_output = await self._async_fn(ctx, *args, **kwargs)
        return ToolOutput(
            content=str(tool_output),
            tool_name=self.metadata.name,
            raw_input={"args": args, "kwargs": kwargs},
            raw_output=tool_output,
        )
