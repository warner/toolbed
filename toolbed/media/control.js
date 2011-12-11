
var yup = 1;

function fill(what, element) {
    $(element).text("updating...");
    $.ajax({type: "POST",
            url: "/control/api",
            contentType: "text/json", // what we send
            data: JSON.stringify({token: token, what: what}),
            // data: {a:foo,b:bar} makes .ajax to serialize like "a=foo&b=bar"
            dataType: 'json', // what we expect, and how to parse it
            success: function(data) { $(element).text(data.text); }
           });
};

$(function() {
      $("#tabs").tabs({selected: -1});
      $("#tabs").bind('tabsshow', function(event, ui)
                      {
                          //alert(ui.index);
                          //$("#webport").text("fetching..");
                          fill("webport", "#webport");
                          return true;
                          });
});
