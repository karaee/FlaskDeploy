import json5
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button
import mpl_toolkits.axes_grid1
from dp import dynaplex
import sys
from enum import Enum
import numpy as np

print(sys.path[0])

colors = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
    '#1f77b4', '#aec7e8', '#ffbb78', '#98df8a', '#ff9896',
    '#c5b0d5', '#c49c94', '#f7b6d2', '#c7c7c7', '#dbdb8d',
    '#9edae5' 
]
ContainerStatus = Enum('ContainerStatus', [('Idle', 0), ('ToOrigin', 1), ('ToDestination', 2), ('ToDepot', 3)])
box_margin = 0.005

def remove_ticks(ax):
    ax.xaxis.set_ticks([])
    ax.xaxis.set_ticklabels([])
    ax.yaxis.set_ticks([])
    ax.yaxis.set_ticklabels([])

class Player(FuncAnimation):
    def __init__(self, fig, func, frames=None, init_func=None, fargs=None,
                 save_count=None, mini=0, maxi=10000, pos=(0.125, 0.92), **kwargs):
        self.i = 0
        self.min=mini
        self.max=min( [maxi, len(frames)])
        self.runs = True
        self.forwards = True
        self.fig = fig
        self.func = func
        self.setup(pos)
        self.setup_kpi_board(pos = [0.65, 0.89], size = [0.25, 0.10])
        self.setup_oo_book()
        self.anim_vars = {'decision_delay':False} 
        fargs = fargs + (self.kpi_board_ax, self.oo_book_ax, self.anim_vars)
        FuncAnimation.__init__(self,self.fig, self.func, frames=self.play(), 
                                           init_func=init_func, fargs=fargs,
                                           save_count=save_count, **kwargs )  

    def play(self):
        while self.runs:
            self.i = self.i+self.forwards-(not self.forwards)
            if self.i > self.min and self.i < self.max:
                yield self.i
            else:
                self.stop()
                yield self.i

    def start(self):
        self.runs=True
        self.event_source.start()
        # Visuals
        self.button_stop.label.set_color('black')
        self.button_stop.ax.figure.canvas.draw_idle()

    def stop(self, event=None):
        self.runs = False
        self.event_source.stop()
        # Visuals
        self.button_stop.label.set_color('gray')
        self.button_stop.ax.figure.canvas.draw_idle()
        


    def forward(self, event=None):
        self.forwards = True
        self.start()
    def backward(self, event=None):
        self.forwards = False
        self.start()
    def oneforward(self, event=None):
        self.forwards = True
        self.onestep()
    def onebackward(self, event=None):
        self.forwards = False
        self.onestep()

    def onestep(self):
        if self.i > self.min and self.i < self.max:
            self.i = self.i+self.forwards-(not self.forwards)
        elif self.i == self.min and self.forwards:
            self.i+=1
        elif self.i == self.max and not self.forwards:
            self.i-=1
        self.func(self.i, *self._args)
        self.fig.canvas.draw_idle()

    def setup(self, pos):
        playerax = self.fig.add_axes( [pos[0],pos[1], 0.22, 0.04])
        divider = mpl_toolkits.axes_grid1.make_axes_locatable(playerax)
        bax = divider.append_axes("right", size="80%", pad=0.05)
        sax = divider.append_axes("right", size="80%", pad=0.05)
        fax = divider.append_axes("right", size="80%", pad=0.05)
        ofax = divider.append_axes("right", size="100%", pad=0.05)
        self.button_oneback = Button(playerax, label=u'$\u29CF$')
        self.button_back = Button(bax, label=u'$\u25C0$')
        self.button_stop = Button(sax, label=u'$\u25A0$')
        self.button_forward = Button(fax, label=u'$\u25B6$')
        self.button_oneforward = Button(ofax, label=u'$\u29D0$')
        self.button_oneback.on_clicked(self.onebackward)
        self.button_back.on_clicked(self.backward)
        self.button_stop.on_clicked(self.stop)
        self.button_forward.on_clicked(self.forward)
        self.button_oneforward.on_clicked(self.oneforward)

    def setup_kpi_board(self, pos, size):
        self.kpi_board_ax = self.fig.add_axes([pos[0], pos[1], size[0], size[1]])
        remove_ticks(self.kpi_board_ax)
        for spine in self.kpi_board_ax.spines.values():
            spine.set_linestyle('--')  # Set dashed style
            spine.set_color('gray')    # Set color (optional)

    def setup_oo_book(self):
        main_ax_pos = self.fig.axes[0].get_position() 
        self.oo_book_ax = self.fig.add_axes([0 + box_margin , main_ax_pos.y0, main_ax_pos.x0 - 2*box_margin, main_ax_pos.height])
        remove_ticks(self.oo_book_ax)
        for spine in self.oo_book_ax.spines.values():
            spine.set_linestyle('--')  # Set dashed style
            spine.set_color('gray')    # Set color (optional)


def visualize_dynamic_world(iter, trace, configs, ax, kpi_board_ax, oo_book_ax, anim_vars):
    # region Initial steps
    wSize = configs["world_dimensions"]
    nOrder = trace[iter]["period_count"]
    dynamic_state = trace[iter]["state"]
    depot_stocks = { d["key"] : {t["key"]:0 for t in configs["container_types"]    }   for d in configs["depots"]}
        
    if 'action' in trace[iter]:
        action = trace[iter]['action']
    else: action = -1

    # Get state variables
    time = dynamic_state["current_time"]
    cat = dynamic_state["cat"]
    orders = dynamic_state["orders"]
    containers = dynamic_state["containers"]
    SEQ = dynamic_state["scheduled_event_queue"]
    
    ax.clear()  # Clear previous drawings to update with new state
    kpi_board_ax.clear()
    oo_book_ax.clear()
    remove_ticks(ax)
    remove_ticks(kpi_board_ax)
    remove_ticks(oo_book_ax)
    ax.set_xlim(0, wSize[0])
    ax.set_ylim(0, wSize[1])

    # Constants for layout
    box_height = 0.6
    box_width = 2.0
    start_y = 5
    padding_x = 0.05 * wSize[0]
    padding_y = 0.03 * wSize[1]
    OD_icon_size = 0.02 * wSize[1]
    oo_book_ratio = oo_book_ax.get_position().height/oo_book_ax.get_position().width
    world_ratio = ax.get_position().height/ax.get_position().width
    ctrSize = 1.5
    # endregion

    # region UI elements
    # Draw KPI board
    rew_text = f"Reward incurred:       {trace[iter]['incr_return']}"
    tot_rew_text = f"Total reward:      {trace[iter]['cum_return']}"
    lost_sale_text = f"Total lost sales:        {dynamic_state['total_lost_sales']}"
    kpi_board_ax.text(0, 1 - 0.2, rew_text, fontsize=10, ha='left', va = 'center')
    kpi_board_ax.text(0, 0.66 - 0.2, tot_rew_text, fontsize=10, ha='left', va = 'center')
    kpi_board_ax.text(0, 0.33 - 0.2, lost_sale_text, fontsize=10, ha='left', va = 'center')
    
    # Title (time, order# and action)
    message = "\n"
    if anim_vars['decision_delay']:
        anim_vars['decision_delay'] = False
        if not ("index" in cat and cat["index"] == 12):
            message += "Decision is delayed. "

    eventOrder = -1
    if cat["await"] == "action":
        message = f"\nTaking action for O{dynamic_state['decision_order_id']}!"
        if action == len(containers) and SEQ[0]["payload_type"] != 2:
            anim_vars['decision_delay'] = True

    else:
        if "index" in cat:
            if cat["index"] == 11:
                action = str(SEQ[0]["action_index"])
                eventOrder = str(SEQ[0]["order_index"])
                message += f"C{action} assigned to O{eventOrder}."
                event_order_color = 'green'  
            elif cat["index"] == 12:
                eventOrder = str(SEQ[0]["lost_order_id"])
                event_order_color = 'red'
                message += f"O{eventOrder} is lost!"
            elif cat["index"] == 13:
                action = str(SEQ[0]["action_index"])
                message += f"Container {action} at origin."
            elif cat["index"] == 14:
                action = str(SEQ[0]["action_index"])
                message += f"Container {action} at destination."
            elif cat["index"] == 15:
                eventOrder = str(SEQ[0]["order_index"])
                event_order_color = 'yellow'
                message += f"Delayed decision for O{eventOrder} will be taken at {SEQ[0]['trigger_time']}!"
            else:
                raise Exception("Unexpected awaiting event index!")
        else:
            message += f"Waiting for order arrival"
    ax.set_title(f"Current time: {time}\n Order count: {nOrder}{message}")
    # endregion

    for c in containers:
        type_id = int(containers[c]["type_key"])
        if containers[c]["status"] == ContainerStatus.Idle.value:
            depot_stocks[containers[c]["depot_key"]][containers[c]["type_key"]] += 1
        else:
            new_loc = np.array(containers[c]["location"]["coords"])
            old_loc = np.array(containers[c]["oldLocation"]["coords"])
            ax.plot( [new_loc[0], old_loc[0]], [new_loc[1], old_loc[1]], color= colors[type_id], linewidth=0.5, linestyle='--')

            [ctrLoc, alpha] = [(new_loc + old_loc)/2, 0.2]
            anchor = [ctrLoc[0]-ctrSize/2, ctrLoc[1]-ctrSize/2]
            square = patches.Rectangle(anchor, ctrSize, ctrSize, color = colors[type_id], alpha = alpha)
            ax.add_patch(square)
            ax.text( ctrLoc[0],ctrLoc[1] - padding_y , c, color = colors[type_id], ha = 'center', va = 'center')
            if containers[c]["status"] != ContainerStatus.ToDepot.value:
                ord = str(containers[c]["assigned_order_id"])
                O = orders[ord]["o"]["coords"]
                D = orders[ord]["d"]["coords"]
                ax.text(*O, f'O', color=colors[type_id], ha = 'center', va = 'center')
                ax.text(*D, f'D', color=colors[type_id], ha = 'center', va = 'center')
                if containers[c]["status"] == ContainerStatus.ToOrigin.value:
                    ax.plot( [O[0], D[0]], [O[1], D[1]], color= colors[type_id], linewidth=0.5, linestyle='--')

    if orders != None:
        oo_book_cursor_pos = [padding_x/wSize[0], 1 - padding_y/wSize[1]]
        for order in orders:
            if orders[order]["assigned_container_id"] != -1:
                continue
            if int(order) == eventOrder:
                color = event_order_color
                eventOrder = -1
            else:   
                color = 'black'
            origin = orders[order]["o"]["coords"]
            destination = orders[order]["d"]["coords"]
            orderType = orders[order]["type_key"]
            ax.annotate('', destination, origin, arrowprops=dict(arrowstyle='->', linestyle='--', color=color, linewidth=0.5))

            oo_book_ax.text(*oo_book_cursor_pos, f"Order {order}, DL: {orders[order]['due_date']}", fontsize=10, ha='left', va = 'bottom')
            cont_options = [ o_t["container_type_options"] for o_t in configs["order_types"] if o_t["key"] == orderType][0]
            for i in range(len(cont_options)):
                color = colors[int(cont_options[i])]
                # Calculate angle for each stripe
                angle_start = (i / len(cont_options)) * 360 + 90
                angle_end = ((i + 1) / len(cont_options)) * 360 + 90
                # Create a wedge (section of the circle)
                wedge = patches.Wedge(origin, OD_icon_size/2, angle_start, angle_end, color=color)
                ax.add_patch(wedge)
                rect = patches.Rectangle([1-oo_book_cursor_pos[0]-10/wSize[0]*(1-i/len(cont_options)), oo_book_cursor_pos[1]],
                                         1/len(cont_options)*10/wSize[0], 10/wSize[0]/oo_book_ratio ,color = color)
                oo_book_ax.add_patch(rect)
            oo_book_cursor_pos[1] -= padding_y/wSize[1]

    for depot in depot_stocks:
        loc = configs["depots"][int(depot)-1]["location"]["coords"]
        nChars = 2*(len(depot_stocks[depot].keys())-1)+1
        padding_char = wSize[0] * 0.005
        pos = 0 - (nChars/2) * padding_char
        for typ in depot_stocks[depot]:
            txt = depot_stocks[depot][typ]
            color = colors[int(typ)]
            ax.text(loc[0] + pos, loc[1], txt, color=color, ha = 'center', va = 'center')
            ax.text(loc[0] + pos + padding_char, loc[1] - padding_y, " ", color='black', ha = 'center', va = 'center')
            pos = pos + 2*padding_char
        circle = patches.Circle(loc, 1.5*ctrSize, edgecolor = 'black', facecolor='none')
        ax.add_patch(circle)

folder_name = "container_allocation"
policy_number = 0
mdp_version_number = 0
path_to_json = dynaplex.filepath("mdp_config_examples", folder_name, f"mdp_config_{mdp_version_number}.json")
try:
    with open(path_to_json, "r") as input_file:
        configs = json5.load(input_file)    # configs can be initialized manually with something like
except FileNotFoundError:
    raise FileNotFoundError(f"File {path_to_json} not found. Please make sure the file exists and try again.")
except:
    raise Exception("Something went wrong when loading the json file. Have you checked the json file does not contain any comment?")

mdp = dynaplex.get_mdp(**configs)
# policy = mdp.get_policy("DelayAlways")
# policy = mdp.get_policy("random")
policy = mdp.get_policy("GreedyPolicy")
demonstrator = dynaplex.get_demonstrator(max_period_count=100)
trace = demonstrator.get_trace(mdp, policy)

# nContainer = len(configs['initialLocations'] )

# Setup figure and axes for the animation
fig, ax = plt.subplots(figsize=(16, 9))
for spine in ax.spines.values():
    spine.set_linestyle('--')  # Set dashed style
    spine.set_color('gray')    # Set color (optional)
remove_ticks(ax)
# Create the animation
ani = Player(fig, visualize_dynamic_world, frames=range(1, 500), fargs=(trace, configs, ax), repeat=False, interval = 200)

# with open("myvideo.html", "w") as f:
#     print(ani.to_html5_video(), file=f)

# ani.save(dynaplex.filepath("movies","animation.gif"), writer='Pillow', fps=2)
plt.show()
