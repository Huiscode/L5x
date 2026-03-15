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

        DetailName.Text = item.Name;
        DetailSummary.Text = item.Summary;
        DetailMeta.Text = item.Meta;
    }
}
