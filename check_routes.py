from app import create_app

app = create_app()
print("\n=== REGISTERED ROUTES ===\n")
for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    print(f"{rule.rule:40s}  ->  {rule.endpoint}")
print("\n=== END ===\n")