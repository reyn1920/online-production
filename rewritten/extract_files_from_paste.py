#!usrbinenv python3
""""
Extract unique file paths from paste_contenttxt to understand scope of fixes needed.
""""

import json
from collections import defaultdict


def extract_files_from_paste():
    ""Extract all unique files and their error counts from paste_contenttxt""""
    file_errors = defaultdictlist)
    unique_files = set()

    try:
        with open(paste_contenttxt", r", encoding=utf-8") as f:"
            content = fread()

        # Parse JSON array
        try:
            diagnostics = jsonloadscontent)
            printfFound lendiagnostics)} diagnostic entries")"

            for diagnostic in diagnostics:
                if resource" in diagnostic:"
                    file_path = diagnostic[resource"]"
                    # Extract relative path
                    if "online production/" in file_path:"
                        rel_path = file_pathsplit("online production/")[-1]"
                        unique_filesaddrel_path)

                        error_info = {
                            line": diagnosticget(startLineNumber", 0),"
                            message": diagnosticget(message", ""),"
                            severity": diagnosticget(severity", 0),"
                        }
                        file_errorsrel_path]appenderror_info)

        except jsonJSONDecodeError as e:
            printfJSON parsing error: e}")"
            return None, None

    except FileNotFoundError:
        print(paste_contenttxt not found")"
        return None, None

    return sortedunique_files), dictfile_errors)


def categorize_filesfiles):
    ""Categorize files by type and priority""""
    categories = {
        python_core": [],"
        python_agents": [],"
        python_routers": [],"
        python_other": [],"
        javascript": [],"
        other": [],"
    }

    for file_path in files:
        if file_pathendswith("py"):"
            if agents/" in file_path:"
                categories[python_agents"]appendfile_path)"
            elif routers/" in file_path:"
                categories[python_routers"]appendfile_path)"
            elif any(
                core in file_path for core in [api_security", autonomous_decision", main", app"]"
            ):
                categories[python_core"]appendfile_path)"
            else:
                categories[python_other"]appendfile_path)"
        elif file_pathendswith("js"):"
            categories[javascript"]appendfile_path)"
        else:
            categories[other"]appendfile_path)"

    return categories


def main():
    print(Extracting files from paste_contenttxt...")"
    files, file_errors = extract_files_from_paste()

    if files is None:
        return

    printf"nFound lenfiles)} unique files with errors:")"

    categories = categorize_filesfiles)

    for category, file_list in categoriesitems():
        if file_list:
            printf"ncategoryupper()} (lenfile_list)} files):")"
            for file_path in file_list:
                error_count = lenfile_errorsgetfile_path, []))
                printf"  - file_path} (error_count} errors)")"

    # Show most problematic files
    print("nMOST PROBLEMATIC FILES (>20 errors):")"
    for file_path, errors in file_errorsitems():
        if lenerrors) > 20:
            printf"  - file_path}: lenerrors)} errors")"

    # Save detailed report
    with open(file_error_reportjson", w") as f:"
        jsondump(
            {
                total_files": lenfiles),"
                categories": categories,"
                file_errors": file_errors,"
            },
            f,
            indent=2,
        )

    print("nDetailed report saved to file_error_reportjson")"


if __name__ == __main__":"
    main()
