import pcbnew
import os
import sys
import inspect

class RuleManagerPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Kicad Rule Converter v1.0"
        self.category = "Utility"
        self.description = "Altium RUL converter and KiCad rule transfer (Designed by Muzaffer Nizam)"
        self.show_toolbar_button = True 
        
        # --- İkon Yükleyici (Tekrar Aktif) ---
        try:
            plugin_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            plugin_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
            
        self.icon_file_name = os.path.join(plugin_dir, 'icon.png')

    def Run(self):
        import wx
        import re
        import shutil
        import csv
        import traceback

        class RuleManagerDialog(wx.Dialog):
            def __init__(self, parent, current_board_dir):
                super().__init__(parent, title="KiCad Rule Converter v1.0", size=(720, 550), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
                self.current_board_dir = current_board_dir
                self.unconverted_data = [] 
                self.InitUI()

            def InitUI(self):
                panel = wx.Panel(self)
                vbox = wx.BoxSizer(wx.VERTICAL)

                hbox1 = wx.BoxSizer(wx.HORIZONTAL)
                st_input = wx.StaticText(panel, label="Source File (.RUL or .kicad_dru):")
                hbox1.Add(st_input, flag=wx.RIGHT, border=8)
                vbox.Add(hbox1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)

                hbox2 = wx.BoxSizer(wx.HORIZONTAL)
                self.tc_input = wx.TextCtrl(panel)
                btn_browse_in = wx.Button(panel, label="Browse")
                btn_browse_in.Bind(wx.EVT_BUTTON, self.OnBrowseInput)
                hbox2.Add(self.tc_input, proportion=1)
                hbox2.Add(btn_browse_in, flag=wx.LEFT, border=5)
                vbox.Add(hbox2, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)

                hbox3 = wx.BoxSizer(wx.HORIZONTAL)
                st_output = wx.StaticText(panel, label="Target KiCad Project Directory:")
                hbox3.Add(st_output, flag=wx.RIGHT, border=8)
                vbox.Add(hbox3, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=5)

                hbox4 = wx.BoxSizer(wx.HORIZONTAL)
                self.tc_output = wx.TextCtrl(panel)
                if self.current_board_dir:
                    self.tc_output.SetValue(self.current_board_dir)
                    
                btn_browse_out = wx.Button(panel, label="Browse")
                btn_browse_out.Bind(wx.EVT_BUTTON, self.OnBrowseOutput)
                hbox4.Add(self.tc_output, proportion=1)
                hbox4.Add(btn_browse_out, flag=wx.LEFT, border=5)
                vbox.Add(hbox4, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)

                st_log = wx.StaticText(panel, label="Unconverted Rules (Requires Manual Definition):")
                vbox.Add(st_log, flag=wx.LEFT|wx.TOP, border=5)

                self.list_ctrl = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.BORDER_SUNKEN)
                self.list_ctrl.InsertColumn(0, "#", width=40)
                self.list_ctrl.InsertColumn(1, "Altium Rule Name", width=140)
                self.list_ctrl.InsertColumn(2, "Rule Type", width=130)
                self.list_ctrl.InsertColumn(3, "KiCad Definition Location (Suggestion)", width=350)
                
                vbox.Add(self.list_ctrl, proportion=1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP|wx.BOTTOM, border=10)

                lbl_designer = wx.StaticText(panel, label="Designed by Muzaffer Nizam")
                font = lbl_designer.GetFont()
                font.SetStyle(wx.FONTSTYLE_ITALIC)
                lbl_designer.SetFont(font)
                lbl_designer.SetForegroundColour(wx.Colour(100, 100, 100))
                vbox.Add(lbl_designer, flag=wx.ALIGN_RIGHT|wx.RIGHT|wx.BOTTOM, border=5)

                hbox_btns = wx.BoxSizer(wx.HORIZONTAL)
                btn_process = wx.Button(panel, label="Convert / Transfer")
                btn_process.Bind(wx.EVT_BUTTON, self.OnProcess)
                
                self.btn_export = wx.Button(panel, label="Export to CSV")
                self.btn_export.Bind(wx.EVT_BUTTON, self.OnExportCSV)
                self.btn_export.Enable(False) 
                
                btn_close = wx.Button(panel, label="Close")
                btn_close.Bind(wx.EVT_BUTTON, self.OnClose)
                
                hbox_btns.Add(btn_process, flag=wx.RIGHT, border=10)
                hbox_btns.Add(self.btn_export, flag=wx.RIGHT, border=10)
                hbox_btns.Add(btn_close)
                vbox.Add(hbox_btns, flag=wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, border=10)

                panel.SetSizer(vbox)

            def OnBrowseInput(self, event):
                wildcard = "Supported Files (*.RUL;*.kicad_dru)|*.RUL;*.kicad_dru|Altium RUL (*.RUL)|*.RUL|KiCad Rules (*.kicad_dru)|*.kicad_dru"
                dlg = wx.FileDialog(self, "Select Source Rule File", "", "", wildcard, wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
                if dlg.ShowModal() == wx.ID_OK:
                    self.tc_input.SetValue(dlg.GetPath())
                dlg.Destroy()

            def OnBrowseOutput(self, event):
                dlg = wx.DirDialog(self, "Select Target KiCad Project Directory", self.tc_output.GetValue(), wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
                if dlg.ShowModal() == wx.ID_OK:
                    self.tc_output.SetValue(dlg.GetPath())
                dlg.Destroy()

            def OnClose(self, event):
                self.EndModal(wx.ID_CANCEL)

            def get_target_dru_name(self, target_dir):
                for f in os.listdir(target_dir):
                    if f.endswith('.kicad_pcb') or f.endswith('.kicad_pro'):
                        return os.path.splitext(f)[0] + '.kicad_dru'
                return 'custom_rules.kicad_dru'

            def ShowErrorDialog(self, traceback_str):
                err_dlg = wx.Dialog(self, title="System Exception Caught!", size=(650, 450))
                err_vbox = wx.BoxSizer(wx.VERTICAL)
                
                lbl = wx.StaticText(err_dlg, label="An error occurred during the conversion process.\nPlease check the traceback below:")
                err_vbox.Add(lbl, flag=wx.ALL, border=10)
                
                tc = wx.TextCtrl(err_dlg, style=wx.TE_MULTILINE | wx.TE_READONLY)
                tc.SetValue(traceback_str)
                err_vbox.Add(tc, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)
                
                btn = wx.Button(err_dlg, label="Close")
                btn.Bind(wx.EVT_BUTTON, lambda e: err_dlg.Destroy())
                err_vbox.Add(btn, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=10)
                
                err_dlg.SetSizer(err_vbox)
                err_dlg.ShowModal()

            def OnProcess(self, event):
                try:
                    in_file = self.tc_input.GetValue()
                    out_dir = self.tc_output.GetValue()

                    if not os.path.isfile(in_file):
                        wx.MessageBox("Please select a valid source file.", "Error", wx.OK | wx.ICON_ERROR)
                        return
                    if not os.path.isdir(out_dir):
                        wx.MessageBox("Please select a valid target directory.", "Error", wx.OK | wx.ICON_ERROR)
                        return

                    target_dru_path = os.path.join(out_dir, self.get_target_dru_name(out_dir))
                    
                    self.list_ctrl.DeleteAllItems()
                    self.unconverted_data.clear()
                    self.btn_export.Enable(False)

                    if in_file.lower().endswith('.rul'):
                        dru_content, unconverted = self.parse_and_convert(in_file)
                        with open(target_dru_path, 'w', encoding='utf-8') as f:
                            f.write(dru_content)
                        
                        for i, item in enumerate(unconverted, start=1):
                            row_data = [str(i), item[0], item[1], item[2]]
                            self.unconverted_data.append(row_data)
                            
                            index = self.list_ctrl.InsertItem(self.list_ctrl.GetItemCount(), str(i))
                            self.list_ctrl.SetItem(index, 1, str(item[0]))
                            self.list_ctrl.SetItem(index, 2, str(item[1]))
                            self.list_ctrl.SetItem(index, 3, str(item[2]))

                        if self.unconverted_data:
                            self.btn_export.Enable(True)

                        wx.MessageBox(f"Altium .RUL file successfully converted!\n\nFile:\n{target_dru_path}", "Success", wx.OK | wx.ICON_INFORMATION)
                    
                    elif in_file.lower().endswith('.kicad_dru'):
                        shutil.copy2(in_file, target_dru_path)
                        wx.MessageBox(f"KiCad rule file successfully copied to target!\n\nFile:\n{target_dru_path}", "Success", wx.OK | wx.ICON_INFORMATION)
                    else:
                        wx.MessageBox("Unsupported file format.", "Error", wx.OK | wx.ICON_ERROR)

                except Exception as e:
                    error_trace = traceback.format_exc()
                    self.ShowErrorDialog(error_trace)

            def OnExportCSV(self, event):
                if not self.unconverted_data:
                    return
                dlg = wx.FileDialog(self, "Save CSV File", "", "Unconverted_Rules.csv", "CSV Files (*.csv)|*.csv", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
                if dlg.ShowModal() == wx.ID_OK:
                    path = dlg.GetPath()
                    try:
                        with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                            writer = csv.writer(f, delimiter=';') 
                            writer.writerow(["No", "Altium Rule Name", "Rule Type", "KiCad Definition Location (Suggestion)"])
                            writer.writerows(self.unconverted_data)
                        wx.MessageBox("CSV file successfully saved!", "Success", wx.OK | wx.ICON_INFORMATION)
                    except Exception as e:
                        wx.MessageBox(f"An error occurred while saving CSV:\n{str(e)}", "Error", wx.OK | wx.ICON_ERROR)
                dlg.Destroy()

            def read_file_robust(self, filepath):
                encodings = ['utf-8-sig', 'utf-16', 'windows-1254', 'windows-1251', 'iso-8859-1']
                for enc in encodings:
                    try:
                        with open(filepath, 'r', encoding=enc) as f:
                            return f.read()
                    except Exception:  # UnicodeError dahil TÜM hataları yakalar ve çökmeyi önler!
                        continue
                
                # Hiçbiri tutmazsa son çare: Hatalı karakterleri yoksayarak UTF-8 aç
                with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                    return f.read()

            def parse_and_convert(self, rul_path):
                content = self.read_file_robust(rul_path)

                rules = ["(version 1)", ""]
                unconverted_rules = []
                lines = content.split('ś') if 'ś' in content else content.splitlines()
                
                for line in lines:
                    if "RULEKIND=" not in line:
                        continue
                        
                    params = {}
                    for part in line.split('|'):
                        if '=' in part:
                            try:
                                k, v = part.split('=', 1)
                                params[k] = v
                            except ValueError:
                                pass
                            
                    rule_kind = params.get("RULEKIND", "")
                    name = params.get("NAME", "Custom_Rule").strip()
                    enabled = params.get("ENABLED", "TRUE").strip()
                    
                    if enabled != "TRUE":
                        continue
                        
                    scope1 = params.get("SCOPE1EXPRESSION", "All")
                    condition = self.extract_kicad_condition(scope1)
                    
                    if rule_kind == "Clearance":
                        gap = self.mil_to_mm(params.get("GAP", "10mil"))
                        rule_text = f'(rule "{name}"\n'
                        if condition: rule_text += f'  (condition "{condition}")\n'
                        rule_text += f'  (constraint clearance (min {gap}))\n)\n'
                        rules.append(rule_text)
                        
                    elif rule_kind == "Width":
                        min_w = self.mil_to_mm(params.get("MINWIDTH", "10mil"))
                        opt_w = self.mil_to_mm(params.get("PREFEREDWIDTH", "10mil"))
                        max_w = self.mil_to_mm(params.get("MAXWIDTH", "10mil"))
                        
                        rule_text = f'(rule "{name}"\n'
                        if condition: rule_text += f'  (condition "{condition}")\n'
                        rule_text += f'  (constraint track_width (min {min_w}) (opt {opt_w}) (max {max_w}))\n)\n'
                        rules.append(rule_text)
                        
                    elif rule_kind == "RoutingVias":
                        dia = self.mil_to_mm(params.get("VIADIAMETER", "20mil"))
                        hole = self.mil_to_mm(params.get("VIAHOLESIZE", "10mil"))
                        
                        rule_text = f'(rule "{name}"\n'
                        if condition: rule_text += f'  (condition "{condition}")\n'
                        rule_text += f'  (constraint via_diameter (min {dia}) (max {dia}))\n'
                        rule_text += f'  (constraint hole_size (min {hole}) (max {hole}))\n)\n'
                        rules.append(rule_text)
                    
                    else:
                        kicad_loc = self.get_kicad_location(rule_kind)
                        unconverted_rules.append((name, rule_kind, kicad_loc))
                        
                return "\n".join(rules), unconverted_rules

            def get_kicad_location(self, rule_kind):
                mapping = {
                    "PolygonConnect": "Board Setup -> Design Rules -> Constraints OR Zone Properties",
                    "SolderMaskExpansion": "Board Setup -> Board Stackup -> Solder Mask/Paste",
                    "PasteMaskExpansion": "Board Setup -> Board Stackup -> Solder Mask/Paste",
                    "PowerPlaneClearance": "Zone Properties (Clearance tab)",
                    "PowerPlaneConnect": "Zone Properties (Pad connection type)",
                    "Length": "Board Setup -> Custom Rules OR Net Inspector",
                    "MatchedLengths": "Board Setup -> Custom Rules",
                    "RoutingLayers": "Board Setup -> Board Editor Layers",
                    "HoleSize": "Board Setup -> Design Rules -> Constraints",
                    "ComponentClearance": "Board Setup -> Custom Rules OR Footprint Courtyard boundaries",
                    "ShortCircuit": "Board Setup -> Custom Rules",
                    "UnpouredPolygon": "Zone Properties -> Allow orphaned copper",
                    "AssemblyTestPointUsage": "Resolved by adding special testpoint footprints",
                    "AssemblyTestpoint": "Resolved by adding special testpoint footprints",
                    "Room": "Determined by Custom Rules -> Area / Enclosure rules",
                    "SilkToSilkClearance": "Board Setup -> Design Rules -> Constraints",
                    "SilkToSolderMaskClearance": "Board Setup -> Design Rules -> Constraints",
                    "DifferentialPairsRouting": "Board Setup -> Net Classes OR Custom Rules"
                }
                return mapping.get(rule_kind, "Board Setup -> Custom Rules (Manual Review)")

            def mil_to_mm(self, val_str):
                try:
                    val = float(val_str.lower().replace('mil', '').strip())
                    return f"{(val * 0.0254):.3f}mm"
                except:
                    return "0.250mm"

            def extract_kicad_condition(self, altium_scope):
                if altium_scope == "All": return None
                
                match = re.search(r"InNetClass\('([^']+)'\)", altium_scope)
                if match: return f"A.NetClass == '{match.group(1)}' || B.NetClass == '{match.group(1)}'"
                    
                match = re.search(r"InDifferentialPairClass\('([^']+)'\)", altium_scope)
                if match: return f"A.NetClass == '{match.group(1)}' || B.NetClass == '{match.group(1)}'"
                    
                match = re.search(r"Net\('([^']+)'\)", altium_scope)
                if match: return f"A.NetName == '{match.group(1)}'"
                    
                return None

        board = pcbnew.GetBoard()
        board_path = board.GetFileName()
        board_dir = os.path.dirname(board_path) if board_path else ""
        
        dialog = RuleManagerDialog(None, board_dir)
        dialog.ShowModal()
        dialog.Destroy()


RuleManagerPlugin().register()
