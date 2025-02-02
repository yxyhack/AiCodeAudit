def gen_text_from_path(g,path):
    text_list=[]
    for index,p in enumerate(path):
        node_data = g.nodes[p]
        # 添加节点
        # G.add_node(source_name, source_name=unit.source_name, desc=unit.source_desc,
        #            start_code_line=unit.start_code_line, end_code_line=unit.end_code_line, name=unit.name,
        #            path=unit.path)
        source_name=node_data.get("source_name")
        target_name=node_data.get("target_name")
        source_code=node_data.get("source_code")
        desc=node_data.get("desc")
        name=node_data.get("name")
        path_name=node_data.get("path")
        text=f"""<路径_{index}>
        源码路径:{path_name}
        源码文件名称:{name}
        调用代码单元名称:{source_name}
        被调用代码单元名称:{target_name}
        当前代码源码:{source_code}
        源码摘要描述:{desc}
        <路径_{index}>"""
        text_list.append(text)
    return "\n".join(text_list)