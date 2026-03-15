using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;

namespace L5XInspector.App.Views;

public sealed partial class AoiUdtPage : Page
{
    public AoiUdtPage()
    {
        InitializeComponent();
    }

    private void OnSelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (AoiUdtList.SelectedItem is not AoiUdtItem item)
            return;

        DetailKind.Text = item.Kind;
        DetailName.Text = item.Name;
        DetailSummary.Text = item.Summary;
        DetailMeta.Text = item.Meta;
        DetailCounts.Text = BuildCountsText(item);
    }

    private void OnFilterAll(object sender, RoutedEventArgs e)
    {
        AppState.ApplyAoiUdtFilter("All");
    }

    private void OnFilterAoi(object sender, RoutedEventArgs e)
    {
        AppState.ApplyAoiUdtFilter("AOI");
    }

    private void OnFilterUdt(object sender, RoutedEventArgs e)
    {
        AppState.ApplyAoiUdtFilter("UDT");
    }

    private void OnFilterTags(object sender, RoutedEventArgs e)
    {
        AppState.ApplyAoiUdtFilter("TAGS");
    }

    private static string BuildCountsText(AoiUdtItem item)
    {
        return item.Kind switch
        {
            "AOI" => $"Parameters: {item.ParameterCount} • Routines: {item.RoutineCount}",
            "UDT" => $"Members: {item.MemberCount}",
            _ => string.Empty
        };
    }
}
