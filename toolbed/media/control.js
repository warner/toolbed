
function doAPI(method, args, callback) {
    $.ajax({type: "POST",
            url: "/control/api",
            contentType: "text/json", // what we send
            data: JSON.stringify({token: token, method: method, args: args}),
            // data: {a:foo,b:bar} makes .ajax to serialize like "a=foo&b=bar"
            dataType: 'json', // what we expect, and how to parse it
            success: callback });
};

function fill(method, element) {
    $(element).text("updating...");
    doAPI(method, {}, function(data) { $(element).text(data.text); });
};

function fill_val(method, element) {
    doAPI(method, {}, function(data) { $(element).val(data.text); });
};

function htoggle(element) {
    $(element).toggle("slide", {direction: "horizontal"});
};

function sendMessage(event) {
    console.log("sendMessage");
    var args = {to: $("#message-to").val(),
                message: $("#message-message").val()
               };
    doAPI("sendMessage", args, function(){alert("Sent!");});
};

function profileSetName(event) {
    var name = $("#profile-name-input").val();
    doAPI("profile-set-name", {"name": name});
    $("#profile-name").text(name);
};

function getAddressBook() {
    doAPI("getAddressBook", {},
          function (data) {
              var book = $("#address-book");
              book.empty();
              for (var i=0; i<data.length; i++) {
                  var d = data[i];
                  var h = $('<li />')
                      .text(d.petname+" ("+d.key+")")
                      .appendTo(book);
              }
          });
};


function togglePendingInvitations() {
    $("#pending-invitations").slideToggle();
};

function cancelInvitation(invite) {
    doAPI("cancelInvitation", invite, getPendingInvitations);
};

function getPendingInvitations() {
    doAPI("getOutboundInvitations", {},
          function (data) {
              $("#count-pending-invitations").text(data.length);
              var pending = $("#pending-invitations ul");
              pending.empty();
              for (var i=0; i<data.length; i++) {
                  var d = data[i];
                  var h = $('<li><a href="#"></a></li>')
                      .appendTo(pending)
                  ;
                  h.find("a")
                      .text(d.petname)
                      .data("invite-number", i)
                      .on("click",
                          function() {var i = $(this).data("invite-number");
                                      $("#pending-invite-"+i).slideToggle();})
                  ;
                  var details = $('<ul/>')
                      .appendTo(h)
                      .hide()
                      .attr("id", "pending-invite-"+i)
                  ;
                  details.append($('<li/>').text("Invitation Code: "+d.code));
                  details.append($('<li/>').text("Sent: "+d.sent));
                  details.append($('<li/>').text("Expires: "+d.expires));
                  details.append($('<li/>')
                                 .html('<a href="#">cancel</a>')
                                 .find("a")
                                 .data("invite", d)
                                 .on("click",
                                     function() {var d = $(this).data("invite");
                                                 cancelInvitation(d);})
                                 );
              }
              if (data.length) {
                  $("#toggle-pending-invitations").slideDown();
                  $("#pending-invite-0").show();
              } else {
                  $("#toggle-pending-invitations").slideUp();
              }
          });
};

function startInvitation(event) {
    doAPI("startInvitation", {});
    $("#invite-prepare-invitation").slideDown(500,
                                             function() {
                                                 $("#invite").slideUp(500);
                                                 });
    $("#invite-to").focus(); // TODO: make 'return' trigger the button
};

function sendInvitation(event) {
    var args = { name: $("#invite-to").val() };
    doAPI("sendInvitation", args, getPendingInvitations);
    $("#pending-invitations").slideDown();
    $("#pending-invite-0").slideDown();
    $("#invite-prepare-invitation").slideUp();
    setTimeout(function() { $("#invite").slideDown("slow"); }, 5000);
};

function acceptInvitation(event) {
    var args = { name: $("#invite-from").val(),
                 code: $("#invite-code").val() };
    $("#invite-from").val("");
    $("#invite-code").val("");
    doAPI("acceptInvitation", args,
          function () {
              $("#tabs").tabs("select", 1);
              });
};

$(function() {
      $("#tabs").tabs({selected: 0,
                       show: function(event, ui)
                       {
                           if (ui.index == 0) {
                               fill("webport", "#webport");
                               fill("relay_location", "#relay_location");
                               fill("relay_connected", "#relay_connected");
                               fill("pubkey", "#pubkey");
                           }
                           else if (ui.index == 2) {
                               getPendingInvitations();
                               getAddressBook();
                           }
                           return true;
                       }
                       });
      $("#send-message").on("click", sendMessage);

      fill("profile-name", "#profile-name");
      fill_val("profile-name", "#profile-name-input");
      $("#profile-name-open-input").on("click", function(e) {
                                           htoggle("#profile-name-input");
                                           htoggle("#profile-name");
                                       });
      $("#profile-name-input").on("keyup", function(e) {
                                      if (e.keyCode == 13) {
                                          profileSetName();
                                          e.target.blur();
                                          htoggle("#profile-name-input");
                                          htoggle("#profile-name");
                                      }
                                      return false;
                                  });
      $("#profile-open-icon-uploader").on("click", function(e) {
                                              $("#profile-icon-uploader").slideToggle();
                                              });
      $("#profile-file-upload").on("change", function(e) {
                                       this.files;
                                       });

      $("#toggle-pending-invitations").on("click", togglePendingInvitations);
      $("#invite input").on("click", startInvitation);
      $("#invite-cancel").on("click", function () {
                                 $("#invite").slideDown(500);
                                 $("#invite-prepare-invitation").slideUp(500);
                                 });
      $("#send-invitation").on("click", sendInvitation);
      $("#accept-invitation").on("click", acceptInvitation);
      var evt = new EventSource("/control/events?token="+token);
      evt.addEventListener("relay-connection-changed",
                           function (e) {
                               var connected = JSON.parse(e.data).message;
                               $("#relay_connected").text(connected ?
                                                          "connected" :
                                                          "not connected");
                               });
      evt.addEventListener("address-book-changed", getAddressBook);
      evt.addEventListener("invitations-changed", getPendingInvitations);
});
