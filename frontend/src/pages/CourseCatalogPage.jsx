import { CourseCatalog } from "../components/courses/CourseCatalog";

export function CourseCatalogPage({ institutionalId = "STU001" }) {
    return (
        <div className="app-container">
            <main className="main-content main-content-wide">
                <header className="page-header">
                    <h1>Course Catalog</h1>
                    <p>Enroll in up to 6 course sections per term (SYS-F-006).</p>
                </header>

                <CourseCatalog institutionalId={institutionalId} />
            </main>
        </div>
    );
}
