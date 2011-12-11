
$(function() {
      $("#tabs").tabs({selected: -1});
      $("#tabs").bind('tabsshow', function(event, ui)
                      {
                          //alert(ui.index);
                          //$("#webport").text("fetching..");
                          //fill("webport", "#webport");
                          return true;
                          });
});
