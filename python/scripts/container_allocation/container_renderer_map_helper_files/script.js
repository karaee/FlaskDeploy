//#region Helpers
var colors = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
    '#1f77b4', '#aec7e8', '#ffbb78', '#98df8a', '#ff9896',
    '#c5b0d5', '#c49c94', '#f7b6d2', '#c7c7c7', '#dbdb8d',
    '#9edae5' 
];

function round(num, precision) {
    const factor = Math.pow(10, precision);
    return Math.round(num * factor) / factor;
  }
//#endregion

//#region UpdateView parameters
var init_params = {
    center:[50, 20],
    zoom: 4
};
var map = L.map('mapid').setView(init_params['center'], init_params['zoom']);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    minZoom: 3,
    maxZoom: 18
}).addTo(map);
var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);
var markers = [];
var currentIndex = 0;
var totalFrames = 1;
var isPlaying = false;
var forwardPlay = true;
var interval;
var fps = 4;
var frame_interval = 1000/fps;
var decision_delay;
var total_lost_sales = 0;
var planning_algorithm_used = false;
//#endregion

setTimeout(() => {
    map.invalidateSize();
}, 500);
socket.emit('request_frame', {"index": currentIndex});

//#region Icons
var depot_icon = L.icon({
    iconUrl: "container_renderer_map_helper_files/img/container-yard.png",
    //shadowUrl: 'leaf-shadow.png',
    iconSize:     [60, 60], // size of the icon
    //shadowSize:   [50, 64], // size of the shadow
    iconAnchor:   [30, 59], // point of the icon which will correspond to marker's location
    //shadowAnchor: [4, 62],  // the same for the shadow
    //popupAnchor:  [-20, 5] // point from which the popup should open relative to the iconAnchor
});

//#endregion

//#region player buttons
function playAnimation() {
    isPlaying = true;
    forwardPlay = true;
    document.getElementById("pauseAnimation-button").disabled = false;
    document.getElementById("nextFrame-button").disabled = false;
    document.getElementById("prevFrame-button").disabled = false;
    document.getElementById("playAnimation-button").disabled = true;
    interval = setInterval(() => { socket.emit('request_frame', {"index": currentIndex}); }, frame_interval);
}
function playBackward() {
    isPlaying = true;
    forwardPlay = false;
    document.getElementById("pauseAnimation-button").disabled = false;
    document.getElementById("nextFrame-button").disabled = false;
    document.getElementById("prevFrame-button").disabled = false;
    document.getElementById("playBackward-button").disabled = true;
    interval = setInterval(() => { socket.emit('request_frame', {"index": currentIndex}); }, frame_interval);
}
function pauseAnimation() {
    isPlaying = false;
    clearInterval(interval);
    document.getElementById("pauseAnimation-button").disabled = true;
    if (currentIndex > 0){
        document.getElementById("playAnimation-button").disabled = false;
        document.getElementById("nextFrame-button").disabled = false;
    }
    else{
        document.getElementById("playAnimation-button").disabled = true;
        document.getElementById("nextFrame-button").disabled = true;
    }
    if (currentIndex < totalFrames - 1){
        document.getElementById("playBackward-button").disabled = false;
        document.getElementById("prevFrame-button").disabled = false;
    }
    else{
        document.getElementById("playBackward-button").disabled = true;
        document.getElementById("prevFrame-button").disabled = true;

    }
}
function nextFrame() {
    currentIndex = currentIndex + 1;
    socket.emit('request_frame', {"index": currentIndex});
    if (currentIndex == totalFrames - 1)
        pauseAnimation();
    else{
        document.getElementById("nextFrame-button").disabled = false;
        document.getElementById("prevFrame-button").disabled = false;
    }
}
function prevFrame() {
    currentIndex = currentIndex - 1;
    socket.emit('request_frame', {"index": currentIndex});
    if (currentIndex == 0)
        pauseAnimation();
    else{
        document.getElementById("nextFrame-button").disabled = false;
        document.getElementById("prevFrame-button").disabled = false;
    }
}
function jumpToFrame() {
    input =  document.getElementById("frameJump-input").value;
    parsed = parseInt(input, 10);
    isInteger = !isNaN(parsed) && String(parsed) === input.trim();
    if (isInteger)
        currentIndex = parsed;
    max_frame = parseInt(document.getElementById("maxFrame").textContent.slice(1), 10);
    document.getElementById("frameJump-input").value = currentIndex % max_frame;
    socket.emit('request_frame', {"index": currentIndex});
    if (currentIndex == 0 || currentIndex == totalFrames - 1)
        pauseAnimation();
}

const textarea = document.getElementById("frameJump-input");
const button = document.getElementById("frameJump-textbox");
textarea.addEventListener("keydown", function(event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault(); // prevent newline
        button.click();         // trigger the button
        }
    });

//#endregion

function updateMarkers(depots, OH, IT, event_order) {
    markers.forEach(m => map.removeLayer(m));
    markers = [];
    depots.forEach(dpt => {
        var title = dpt.key;
        var marker = L.marker(dpt.coords, {icon: depot_icon, title: dpt.key});
        var OH_per_depot = Object.values(OH[dpt.key]);
        var IT_per_depot = Object.values(IT[dpt.key]);
        let tooltipContent = `OH: `
        tooltipContent += OH_per_depot.map((value, index) => {
            return `<span style="color: ${colors[index]}">${value}</span>`;
        }).join(',&nbsp;&nbsp;');
        tooltipContent += `<br>IT: `
        tooltipContent += IT_per_depot.map((value, index) => {
            return `<span style="color: ${colors[index]}">${value}</span>`;
        }).join(',&nbsp;&nbsp;');
        marker.bindTooltip(tooltipContent, {permanent: true, offset: [-30, 1], className: "depot-tooltip"})
        //marker.icon = depot_icon;
        marker.addTo(map);
        markers.push(marker);
    });
    if (event_order !== -1){
        var o = event_order[0];
        var d = event_order[1];
        var c_types = event_order[2];
        var origin_icon = L.divIcon({
            html: c_types,
            className: '',
            iconSize: [30, 30],
            iconAnchor:  [-30, 50]
        });
        var marker = L.marker([o[0],o[1]], {icon: origin_icon, title: "Origin"});
        marker.addTo(map);
        markers.push(marker);

        var angle = Math.atan2(d[1]-o[1], d[0]-o[0]);
        angle = Math.round(angle*180 / Math.PI) - 90;
        icon_html = `<div style= "transform: rotate(` + angle + `deg); transform-origin: 0px 18px;`;
        icon_html += `font-size: 24px; display: inline-block; white-space: nowrap;">------➤</div>`;
        var direction_icon = L.divIcon({
            html: icon_html,
            className: 'd-icon',
            iconSize: null,
            iconAnchor:  [-30, 62]
        });
        var marker = L.marker([o[0],o[1]], {icon: direction_icon, title: "Destination"});
        marker.addTo(map);
        markers.push(marker);
    }

}

function updatePlayerButtons(index, total_frames) {
    switch (index) {
        case 0:
            document.getElementById("nextFrame-button").disabled = false;
            document.getElementById("prevFrame-button").disabled = true;
            document.getElementById("playAnimation-button").disabled = false;
            document.getElementById("playBackward-button").disabled = true;
            return;
        case total_frames-1:
            document.getElementById("nextFrame-button").disabled = true;
            document.getElementById("prevFrame-button").disabled = false;
            document.getElementById("playAnimation-button").disabled = true;
            document.getElementById("playBackward-button").disabled = false;
            return;
        default:
            document.getElementById("nextFrame-button").disabled = false;
            document.getElementById("prevFrame-button").disabled = false;
            document.getElementById("playAnimation-button").disabled = false;
            document.getElementById("playBackward-button").disabled = false;
            return;
    }
}

socket.on('update_view', function(data) {
    if (data.index >= 0 && data.index < data.total_frames) {
        currentIndex = data.index;
        totalFrames = data.total_frames;
        updatePlayerButtons(currentIndex, data.total_frames);

        if (document.getElementById('container-type-legend').innerHTML == "") {
            
        }
        //#region Initial steps
        //const wSize = data.configs["world_dimensions"];
        const nOrder = data["period_count"];
        //const dynamic_state = data["state"];
        const configs = data.configs;
        var action, action_depot, action_type = -1;
        if (data['action'] !== -1){
            action = data['action'];
            if ((action < configs["depots"].length*configs["container_types"].length)){
                action_depot = Math.floor(action / configs["container_types"].length);
                action_depot = configs["depots"][action_depot]["key"];
                action_type = action % configs["container_types"].length;
                action_type = configs["container_types"][action_type]["key"]
            }
        }
    
        //Get state variables
        const time = data["current_time"];
        const cat = data["cat"];
        const orders = data["orders"];
        //const containers = data["containers"]
        const SEQ = data["scheduled_event_queue"];
        const FB = data["foresight_order_buffer"];
        
        //#endregion

        //#region Update info board numbers
        //let frame_text = document.getElementById('frame').innerHTML.replace(/\d+/, currentIndex);
        document.getElementById('frame').innerHTML = currentIndex;
        document.getElementById('frameJump-input').value = currentIndex;
        document.getElementById('time').innerHTML = time;
        document.getElementById('tot-arrv').innerHTML = nOrder;
        document.getElementById('tot-lost-sale').innerHTML = round(data["total_lost"], 4);
        document.getElementById('tot-wait-cost').innerHTML = round(data["total_waiting_cost"], 4);
        document.getElementById('tot-lost-cost').innerHTML = round(data["total_lost_sale_cost"], 4);
        document.getElementById('tot-cost').innerHTML = round(data['cum_return'], 4);
        document.getElementById('incr-cost').innerHTML = round(data['incr_return'], 4);
        //#endregion

        //#region Update info board message (time, order# and action)
        var message = ""
        if (decision_delay){
            decision_delay = false;
            if (!(("index" in cat) && (cat["index"] == 12)))
                message += "Decision is delayed. ";
        }

        var eventOrder = -1;
        var lost_sale = false;

        if (cat["await"] == "action"){  // Order arrival or delayed decision arrival
            eventOrder = data['decision_order_id'];
            if ("index" in cat)
                message = `Re-evaluation for Order ${eventOrder}! `;
            else
                message = `Order ${eventOrder} arrives! `;
            if ((action == configs["depots"].length*configs["container_types"].length))
                message += `Decision delayed.`;
            else if ((action == configs["depots"].length*configs["container_types"].length + 1))
                message += `Order lost.`;
            else
                message += `Container of type ${action_type} assigned from ${action_depot}.`;
        }
        else{
            if ("index" in cat){        // Action
                if (total_lost_sales < data["total_lost"]) {
                    lost_sale = true;
                    total_lost_sales = data["total_lost"];
                    message += "Order is lost! ";
                }
                if (cat["index"] == 1){         // Await delayed decision
                    eventOrder = SEQ[0]["order_index"];
                    message += `Order ${eventOrder} re-evaluation at ${SEQ[0]['trigger_time']}!`;
                }
                else if (cat["index"] == 2){    // Await container arrival
                    container_id = SEQ[0]["action_index"];
                    message += `Container ${container_id} arrived at depot.`;
                }
                else
                    throw new Error("Unexpected awaiting event index!");
            }
            else
                message += "Waiting for new order arrival";
        }
        document.getElementById('state-cat-message').innerHTML = message;
        //#endregion

        //#region Orders
        var selected_types_html = "";
        //console.log(orders);
        var ob_content = `<td colspan="3">Order book is empty</td>`;
        if(orders !== null && orders.length != 0){
            ob_content = "";
            for (const i of Object.keys(orders)) {
                const order = orders[i];
                event_order_style = (i == eventOrder) ? `style="font-weight: bold; color: red;"` : ``;
                new_row = `\n<tr ` + event_order_style + `>\n` +
                    `<td>Order${i}</td>\n` +
                    `<td>due in ${order.due_date-time}</td>\n` + "<td>";
                const options = configs.order_types.find(obj => obj.key === order.type_key).container_type_options;
                selected_types_html = "";
                for (let j = 0; j < configs.container_types.length ; j++){
                    if(options.includes(configs.container_types[j].key)){
                        selected_types_html += `<span style="background-color:${colors[j]}">
                            &nbsp;&nbsp;&nbsp;&nbsp;</span>`;}}
                new_row += selected_types_html + "</td>";
                ob_content += new_row + `\n`;
            }
        }
        document.getElementById('order-book-content').innerHTML = ob_content;
        
        if (eventOrder == -1)
            updateMarkers(configs.depots, data.OH, data.IT, eventOrder);
        else{
            const order = orders[eventOrder];
            var o, d;
            configs.depots.forEach(dpt => {
                if (dpt.key == order.o_key)
                    o = dpt.coords;
                if (dpt.key == order.d_key)
                    d = dpt.coords;
            });
            const options = configs.order_types.find(obj => obj.key === order.type_key).container_type_options;
            selected_types_html = "";
            for (let j = 0; j < configs.container_types.length ; j++)
                if(options.includes(configs.container_types[j].key))
                    selected_types_html += `<span style="background-color:${colors[j]}">
                        &nbsp;&nbsp;.&nbsp;</span>`;
            updateMarkers(configs.depots, data.OH, data.IT,
                [o, d, selected_types_html]);
        }
        //#endregion

        //#region Foresight State
        var selected_types_html = "";
        //console.log(orders);
        var fb_content = `<td colspan="3">Foresight buffer is empty</td>`;
        if(FB !== null && FB.length != 0){
            fb_content = "";
            for (const i of Object.keys(FB)) {
                const order = FB[i];
                new_row = `\n<tr>\n` +
                    `<td>Order ${order.arrival_time}</td>\n` +
                    `<td>due in ${order.due_date-time}</td>\n` + "<td>";
                const options = configs.order_types.find(obj => obj.key === order.type_key).container_type_options;
                selected_types_html = "";
                for (let j = 0; j < configs.container_types.length ; j++){
                    if(options.includes(configs.container_types[j].key)){
                        selected_types_html += `<span style="background-color:${colors[j]}">
                            &nbsp;&nbsp;&nbsp;&nbsp;</span>`;}}
                new_row += selected_types_html + "</td>";
                fb_content += new_row + `\n`;
            }
        }
        document.getElementById('foresight-buffer-content').innerHTML = fb_content;
        
        if (eventOrder == -1)
            updateMarkers(configs.depots, data.OH, data.IT, eventOrder);
        else{
            const order = orders[eventOrder];
            var o, d;
            configs.depots.forEach(dpt => {
                if (dpt.key == order.o_key)
                    o = dpt.coords;
                if (dpt.key == order.d_key)
                    d = dpt.coords;
            });
            const options = configs.order_types.find(obj => obj.key === order.type_key).container_type_options;
            selected_types_html = "";
            for (let j = 0; j < configs.container_types.length ; j++)
                if(options.includes(configs.container_types[j].key))
                    selected_types_html += `<span style="background-color:${colors[j]}">
                        &nbsp;&nbsp;.&nbsp;</span>`;
            updateMarkers(configs.depots, data.OH, data.IT,
                [o, d, selected_types_html]);
        }
        //#endregion
        
        //#region Plan

        // if (plan !== -1){
        //     if (!planning_algorithm_used){
        //         planning_algorithm_used = true;
        //         var planned_orders = {};
        //     }
        //     planned_orders = UpdatePlan(planned_orders, plan, action, orders[eventOrder]);
        // }
        
        //#endregion

        // Show frame number
        if (isPlaying){
            newIndex = currentIndex + (2*forwardPlay-1)
            if (newIndex > 0 && newIndex < data.total_frames-1)
                currentIndex = newIndex;
            else{
                socket.emit('request_frame', {"index": currentIndex});
                isPlaying = false;
                pauseAnimation();
            }
        }

    }

    function UpdatePlan(planned_orders, new_plan, current_action, current_order){
        let revision_happened = false;
        let new_imminent_order = false;
        if (Object.entries(planned_orders).length === 0) {
            planned_orders[current_order["arrival_time"] + '-' + current_order["type_key"]] = {};
            planned_orders[current_order["arrival_time"] + '-' + current_order["type_key"]][int(current_order["decision_time"])] = current_action;
            for (const act_obj of new_plan["scheduled_actions"]) {
                if (act_obj["order_key"] in planned_orders)
                    planned_orders[act_obj["order_key"]] = {};
                planned_orders[act_obj["order_key"]][int(act_obj["time"])] = act_obj["action"];
            }
        }
        else{
            current_order_in_plan = Object.keys(planned_orders)[0];
            if ( current_order["arrival_time"] + '-' + current_order["type_key"]  !== current_order_in_plan)
                new_imminent_order = true;
            if (new_imminent_order){
                new_current_order_key = current_order["arrival_time"] + '-' + current_order["type_key"];
                reordered = { [new_current_order_key]: planned_orders[new_current_order_key] };
                for (const key of Object.keys(planned_orders))
                    if (key !== new_current_order_key) 
                        reordered[key] = planned_orders[key];
                planned_orders = reordered;
            }
            current_action_in_plan = planned_orders[current_order["arrival_time"] + '-' + current_order["type_key"]][int(current_order["decision_time"])];
            if (current_action_in_plan != current_action)
                revision_happened = true;
            if (revision_happened)
                planned_orders[current_order["arrival_time"] + '-' + current_order["type_key"]][int(current_order["decision_time"])] = current_action;
        }
        imminent_order = Object.keys(planned_orders)[0];
        plan_element = document.getElementById('foresight-buffer-content');
        imminent_action_marked = false;
        let output = plan_element.innerHTML;
        for (const [orderKey, actions] of Object.entries(planned_orders)) {
            output += `\n${orderKey}:\t`;
            for (const [time, action] of Object.entries(actions)) {
                if (!imminent_action_marked && orderKey === imminent_order)
                    output += `<span id ="imminent-action">`;
                if (action === configs["depots"].length*configs["container_types"].length)
                    output += "D ";
                else if (action === configs["depots"].length*configs["container_types"].length )
                    output += "L ";
                else
                    output += `${action} `;
                if (!imminent_action_marked && orderKey === imminent_order){
                    output += `</span>`;
                    imminent_action_marked = true;
                }
            }
        }
        document.getElementById("imminent-action").style.fontWeight = "bold" ;
        document.getElementById("imminent-action").style.color =
        revision_happened ? "rgba(255, 0, 0, 0.5)" : "rgba(0, 255, 0, 0.6)";
        return planned_orders;
    }

});