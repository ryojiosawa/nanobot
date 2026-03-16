import pytest

from nanobot.agent.tools.message import MessageTool
from nanobot.bus.events import OutboundMessage


@pytest.mark.asyncio
async def test_message_tool_returns_error_when_no_target_context() -> None:
    tool = MessageTool()
    result = await tool.execute(content="test")
    assert result == "Error: No target channel/chat specified"


@pytest.mark.asyncio
async def test_message_tool_execute_returns_success_string() -> None:
    sent: list[OutboundMessage] = []

    async def capture(msg: OutboundMessage) -> None:
        sent.append(msg)

    tool = MessageTool(
        send_callback=capture,
        default_channel="telegram",
        default_chat_id="123",
    )

    result = await tool.execute(content="hello")

    assert result == "Message sent to telegram:123"
    assert len(sent) == 1
    assert sent[0].content == "hello"


@pytest.mark.asyncio
async def test_message_tool_execute_includes_attachment_count_in_output() -> None:
    async def noop(msg: OutboundMessage) -> None:
        pass

    tool = MessageTool(
        send_callback=noop,
        default_channel="telegram",
        default_chat_id="123",
    )

    result = await tool.execute(content="see attached", media=["/tmp/a.png", "/tmp/b.png"])

    assert result == "Message sent to telegram:123 with 2 attachments"


@pytest.mark.asyncio
async def test_message_tool_execute_returns_error_when_no_callback() -> None:
    tool = MessageTool(default_channel="telegram", default_chat_id="123")
    result = await tool.execute(content="hello")
    assert result == "Error: Message sending not configured"


@pytest.mark.asyncio
async def test_message_tool_execute_returns_error_when_callback_raises() -> None:
    async def failing(_msg: OutboundMessage) -> None:
        raise RuntimeError("network down")

    tool = MessageTool(
        send_callback=failing,
        default_channel="telegram",
        default_chat_id="123",
    )

    result = await tool.execute(content="hello")

    assert result == "Error sending message: network down"


@pytest.mark.asyncio
async def test_message_tool_sent_in_turn_set_after_successful_send() -> None:
    async def noop(msg: OutboundMessage) -> None:
        pass

    tool = MessageTool(
        send_callback=noop,
        default_channel="telegram",
        default_chat_id="123",
    )

    assert tool._sent_in_turn is False
    await tool.execute(content="hello")
    assert tool._sent_in_turn is True


@pytest.mark.asyncio
async def test_message_tool_sent_in_turn_not_set_for_different_target() -> None:
    async def noop(msg: OutboundMessage) -> None:
        pass

    tool = MessageTool(
        send_callback=noop,
        default_channel="telegram",
        default_chat_id="123",
    )

    await tool.execute(content="hello", channel="discord", chat_id="456")

    assert tool._sent_in_turn is False


@pytest.mark.asyncio
async def test_message_tool_start_turn_resets_sent_in_turn() -> None:
    async def noop(msg: OutboundMessage) -> None:
        pass

    tool = MessageTool(
        send_callback=noop,
        default_channel="telegram",
        default_chat_id="123",
    )

    await tool.execute(content="hello")
    assert tool._sent_in_turn is True

    tool.start_turn()
    assert tool._sent_in_turn is False


@pytest.mark.asyncio
async def test_message_tool_execute_channel_and_chat_id_kwargs_override_defaults() -> None:
    sent: list[OutboundMessage] = []

    async def capture(msg: OutboundMessage) -> None:
        sent.append(msg)

    tool = MessageTool(
        send_callback=capture,
        default_channel="telegram",
        default_chat_id="123",
    )

    result = await tool.execute(content="hello", channel="discord", chat_id="456")

    assert result == "Message sent to discord:456"
    assert sent[0].channel == "discord"
    assert sent[0].chat_id == "456"
