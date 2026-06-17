import sys

path = 'c:/Users/pruth/Downloads/Login Signup Flow Design/src/layouts/LogisticLayout.vue'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove 'flex' from root div class:
orig_root = '''    <div
        class=\"logistic-theme min-h-screen bg-background-light dark:bg-background-dark text-gray-900 dark:text-white font-display antialiased flex\">'''
new_root = '''    <div
        class=\"logistic-theme min-h-screen bg-background-light dark:bg-background-dark text-gray-900 dark:text-white font-display antialiased overflow-x-hidden relative\">'''
content = content.replace(orig_root, new_root)

# Remove 'flex-1' and add overflow-x-hidden to main
orig_main = '''        <main class=\"flex-1 ml-64 min-h-screen flex flex-col transition-all duration-300\">'''
new_main = '''        <main class=\"ml-64 min-h-screen flex flex-col transition-all duration-300 overflow-x-hidden\">'''
content = content.replace(orig_main, new_main)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('LogisticLayout patched!')
