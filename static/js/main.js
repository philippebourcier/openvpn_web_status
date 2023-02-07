	let zfoot = `<div class="float-end" style="width: 100%; padding-top: 8px; padding-right: 10px;">
			<form class="row g-3 float-end">
			  <div class="col-auto"><input type="text" class="form-control" id="UserName" placeholder="username"></div>
			  <div class="col-auto"><button type="button" id="createvpn" class="btn btn-primary mb-3">Create VPN Access</button></div>
			</form>
		    </div>`;
	var ctable = new Tabulator("#ctable", {
		height:"100%",
		layout:"fitColumns",
		columns:[
			{title:"User", field:"CN", sorter:"string", width:"15%"},
			{title:"Remote IP Address", field:"RemoteIP", sorter:"string", hozAlign:"left"},
			{title:"Local IP Address", field:"LocalIP", sorter:"string", hozAlign:"left"},
			{title:"Bytes Received", field:"Bytes_Recv", sorter:"string"},
			{title:"Bytes Sent", field:"Bytes_Sent", sorter:"string"},
			{title:"Connected Since", field:"Connected_Since", sorter:"date", hozAlign:"center"}
		]
	});
        var utable = new Tabulator("#utable", {
                height:"100%",
                layout:"fitColumns",
                columns:[
                        {title:"User", field:"CN", sorter:"string", width:"34%"},
                        {title:"Active", field:"State", sorter:"string", width:"33%", formatter:"tickCross", hozAlign:"center", headerHozAlign:"center"},
                        {title:"Revoke", field:"del", formatter:"buttonCross", hozAlign:"center", headerHozAlign:"center", headerSort:false}
                ],
        	initialSort:[ {column:"State", dir:"desc"} ],
		footerElement:zfoot
        });
	function update_table(tablename,URL) {
 	                const xhttp = new XMLHttpRequest();
                        xhttp.open("GET","/"+URL);
                        xhttp.send();
			xhttp.onload = function() {
				if(xhttp.status==200) {
					data=JSON.parse(xhttp.responseText);
                        		tablename.replaceData(data["usr"]);
				}
			};
	}
	$(document).ready(function() {

		$('#modal').modal({backdrop:'static',keyboard:false});

		update_table(utable,"listusr");
		update_table(ctable,"ovpn");
		setInterval(function(){ update_table(ctable,"ovpn"); },10000);

		utable.on("cellClick", function(e,cell){
			CN=cell._cell.row.data.CN;
			State=cell._cell.row.data.State;
			col=cell._cell.column.definition.title;
			if(col=="Revoke" && State=="true") {
				$("#modt").text("Revoke "+CN+"'s certificate and VPN Access ?");
				$("#modb").html('<h4>This action is not reversible.</h4><br><button type="button" id="revoke" class="btn btn-danger btn-lg">DELETE '+CN.toUpperCase()+'</button><br><br>');
				$("#modal").modal('show');
				$("#revoke").click(function() {
					$("#modb").html('<div class="lds-ellipsis"><div></div><div></div><div></div><div></div></div><h4>Processing, please wait...</h4>');
					const xhttp = new XMLHttpRequest();
					xhttp.open("GET","/delusr?user="+CN);
					xhttp.send();
					xhttp.onload = function() {
                                		if(xhttp.status==200) {
                                        		data=JSON.parse(xhttp.responseText);
							$("#modb").html('<h4>Certificate revoked for user '+data.user+'.</h4>');
                                		}
                        		};
				});
			}
		});
		$("#createvpn").click(function() {
			who=$("#UserName").val().replace(/[^a-zA-Z0-9 ]/g,"");
			if(who!="") {
				$("#modt").text("Create "+who+"'s certificate and VPN Access"); 
				$("#modb").html('<h4>What type of VPN access do you want to create for '+who+' ?</h4><br><button type="button" id="go" class="btn btn-success btn-lg">CREATE ACCESS WITH PASSWORD</button><br><br><button type="button" id="gonopass" class="btn btn-warning btn-lg">CREATE ACCESS WITHOUT PASSWORD</button><br><br>');
				$("#modal").modal('show');
				$("#go").click(function() {
					$("#modb").html('<div class="lds-ellipsis"><div></div><div></div><div></div><div></div></div><h4>Processing, please wait...</h4>');
                                	const xhttp = new XMLHttpRequest();
                                	xhttp.open("GET","/newusr?user="+who);
                                	xhttp.send();
                                	xhttp.onload = function() {
                                        	if(xhttp.status==200) {
                                                	data=JSON.parse(xhttp.responseText);
							$("#modb").html('<h4>Config file ready...</h4><h4>Password : '+data.password+'</h4><h4><a href="/dl?user='+who+'" download="vpn-'+who+'.ovpn">Download Config File</a></h4>');
                                        	}
                                	};
				});
				$("#gonopass").click(function() {
                                        $("#modb").html('<div class="lds-ellipsis"><div></div><div></div><div></div><div></div></div><h4>Processing, please wait...</h4>');
                                        const xhttp = new XMLHttpRequest();
                                        xhttp.open("GET","/newusr?user="+who+"&nopass=True");
                                        xhttp.send();
                                        xhttp.onload = function() {
                                                if(xhttp.status==200) {
                                                        data=JSON.parse(xhttp.responseText);
                                                        $("#modb").html('<h4>Config file ready...</h4><h4>Password : none</h4><h4><a href="/dl?user='+who+'" download="vpn-'+who+'.ovpn">Download Config File</a></h4>');
                                                }
                                        };
                                });
			}
		});
		$("#close").click(function() { update_table(utable,"listusr"); });
		$("#topclose").click(function() { update_table(utable,"listusr"); });

	});
