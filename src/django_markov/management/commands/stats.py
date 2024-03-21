from django.db.models import Sum
from django.utils.translation import gettext_lazy as _
from django_typer import TyperCommand
from rich.console import Console
from rich.table import Table

from django_markov.models import MarkovStats, MarkovTextModel


class Command(TyperCommand):
    help = _("Get a count of models and the total sentences generated.")

    def handle(self):
        model_count = MarkovTextModel.objects.filter(data__notnull=True).count()
        total_sentences = MarkovStats.objects.aggregate(Sum("num_sentences"))[
            "num_sentences__sum"
        ]
        total_short_sentences = MarkovStats.objects.aggregate(
            Sum("num_short_sentences")
        )["num_short_sentences__sum"]
        table = Table(title="Generated Sentence Stats", show_header=True)
        table.add_column("Ready Models", style="green")
        table.add_column("Total Sentences", style="magenta")
        table.add_column("Total Short Sentences", style="cyan")
        table.add_row(
            str(model_count), str(total_sentences), str(total_short_sentences)
        )
        console = Console()
        console.print(table)
