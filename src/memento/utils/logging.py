from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

def build_message_table(message_data):
    table = Table(show_header=False, box=None)
    table.add_row("From", f"{message_data.conversation.contact.first_name} {message_data.conversation.contact.last_name}")
    table.add_row("Phone", message_data.conversation.contact.phone_number)
    table.add_row("Message", message_data.body)
    table.add_row("Received at", message_data.received_at)
    return table

def build_attachments_table(attachments):
    if not attachments:
        return None
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Type")
    table.add_column("URL")
    for attachment in attachments:
        table.add_row(attachment.type, attachment.url)
    return table

def print_message_panel(console: Console, message_table):
    console.print(Panel(
        message_table,
        title="[bold blue]MESSAGE RECEIVED[/]",
        border_style="blue"
    ))

def print_attachments_panel(console: Console, attachments_table):
    if attachments_table:
        console.print(Panel(
            attachments_table,
            title="[bold magenta]ATTACHMENTS[/]",
            border_style="magenta"
        ))
    else:
        console.print(Panel(
            Text("No attachments", style="bold red"),
            title="[bold red]NO ATTACHMENTS[/]",
            border_style="red"
        ))

def print_classification_panel(console: Console, classifications):
    console.print(Panel(
        Text("\n".join(classifications), style="bold green"),
        title="[bold green]IMAGE CLASSIFICATIONS[/]",
        border_style="green"
    ))

def print_classification_error(console: Console, error):
    console.print(Panel(
        Text(f"Error classifying message: {error}", style="bold red"),
        title="[bold red]CLASSIFICATION ERROR[/]",
        border_style="red"
    ))

def print_convex_result_panel(console: Console, convex_result):
    table = Table(show_header=True, header_style="bold green")
    table.add_column("Key")
    table.add_column("Value")
    if isinstance(convex_result, dict):
        items = convex_result.items()
    elif hasattr(convex_result, "__dict__"):
        items = convex_result.__dict__.items()
    else:
        items = [("Result", str(convex_result))]
    for key, value in items:
        table.add_row(str(key), str(value))
    console.print(Panel(
        table,
        title="[bold green]CONVEX RESULT[/]",
        border_style="green"
    ))