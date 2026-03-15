using Microsoft.UI.Xaml.Controls;

namespace L5XInspector.App.Views;

public sealed partial class ImpactPage : Page
{
    public ImpactPage()
    {
        InitializeComponent();
    }

    private void OnSelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (ImpactList.SelectedItem is not ImpactItem item)
            return;

        ImpactDetailName.Text = item.Name;
        ImpactDetailMeta.Text = item.Meta;
        ImpactDetailInfo.Text = item.Detail;
    }
}
