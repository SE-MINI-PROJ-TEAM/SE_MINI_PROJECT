import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch } from "../../api/client";
import { Alert } from "../common/Alert";
import { Button } from "../common/Button";
import "./CourseCatalog.css";

const AVAILABILITY_LABEL = { open: "Open", full: "Full", closed: "Closed" };

// DEV ONLY: the backend identifies the student from the X-Student-Id header
// while ALLOW_INSECURE_DEV_IDENTITY=true. Replace with the real login token
// once authentication exists (see backend/modules/courses/identity.py).
const identityHeaders = (institutionalId) => ({ "X-Student-Id": institutionalId });

export function CourseCatalog({ institutionalId = "STU001" }) {
    const [courses, setCourses] = useState([]);
    const [mine, setMine] = useState({ limit: 6, countsByTerm: {}, enrollments: [] });
    const [term, setTerm] = useState("");
    const [loading, setLoading] = useState(true);
    const [loadError, setLoadError] = useState("");
    const [notice, setNotice] = useState(null); // { type, message }
    const [pendingId, setPendingId] = useState(null);

    // A ref (not state) so a fast double-click cannot send a second request
    // before React re-renders the disabled button.
    const submitting = useRef(false);

    const loadAll = useCallback(async () => {
        try {
            const [catalog, myData] = await Promise.all([
                apiFetch("/api/v1/courses"),
                apiFetch("/api/v1/enrollments/me", {
                    headers: identityHeaders(institutionalId),
                }),
            ]);
            setCourses(catalog.courses);
            setMine(myData);
            setTerm((current) => current || catalog.courses[0]?.term || "");
            setLoadError("");
        } catch (err) {
            setLoadError(`${err.message} Please check that the Flask server is running.`);
        } finally {
            setLoading(false);
        }
    }, [institutionalId]);

    useEffect(() => {
        loadAll();
    }, [loadAll]);

    const handleEnroll = async (course) => {
        if (submitting.current) return;
        submitting.current = true;
        setPendingId(course.id);
        setNotice(null);

        try {
            await apiFetch("/api/v1/enrollments", {
                method: "POST",
                headers: identityHeaders(institutionalId),
                body: JSON.stringify({ courseId: course.id }),
            });
            // Re-read from the server so the screen always matches the database.
            await loadAll();
            setNotice({
                type: "success",
                message: `Enrolled in ${course.code} section ${course.sectionCode}.`,
            });
        } catch (err) {
            // 404/409: the data on screen is stale (e.g. someone took the last
            // seat). Show the server's reason, then re-sync.
            if (err.status === 404 || err.status === 409) {
                await loadAll();
            }
            setNotice({ type: "error", message: err.message });
        } finally {
            submitting.current = false;
            setPendingId(null);
        }
    };

    if (loading) {
        return (
            <div className="card spinner-container">
                <p>Loading course catalog...</p>
            </div>
        );
    }

    const terms = [...new Set(courses.map((c) => c.term))];
    const visible = courses.filter((c) => c.term === term);
    const enrolledIds = new Set(mine.enrollments.map((e) => e.courseId));
    const count = mine.countsByTerm[term] || 0;
    const atLimit = count >= mine.limit;
    const myInTerm = mine.enrollments.filter((e) => e.term === term);

    const actionFor = (course) => {
        if (enrolledIds.has(course.id)) return <span className="catalog-note">Enrolled</span>;
        if (course.availability === "closed") return <span className="catalog-note">Closed for enrollment</span>;
        if (course.availability === "full") return <span className="catalog-note">No seats left</span>;
        if (atLimit) return <span className="catalog-note">Course limit reached</span>;
        return (
            <Button onClick={() => handleEnroll(course)} disabled={pendingId !== null}>
                {pendingId === course.id ? "Enrolling..." : "Enroll"}
            </Button>
        );
    };

    return (
        <div className="card">
            <Alert type="error" message={loadError} />

            <div className="catalog-toolbar">
                <label className="catalog-term">
                    Term
                    <select
                        className="input-control"
                        value={term}
                        onChange={(e) => setTerm(e.target.value)}
                        disabled={terms.length === 0}
                    >
                        {terms.map((t) => (
                            <option key={t} value={t}>{t}</option>
                        ))}
                    </select>
                </label>
                <strong className={atLimit ? "catalog-count catalog-count-full" : "catalog-count"}>
                    Enrolled: {count} / {mine.limit}
                </strong>
                <Button variant="secondary" onClick={loadAll}>Refresh</Button>
            </div>

            {notice && <Alert type={notice.type} message={notice.message} />}

            <div className="catalog-table-wrap">
                <table className="catalog-table">
                    <caption className="sr-only">Course sections and available seats</caption>
                    <thead>
                        <tr>
                            <th scope="col">Course</th>
                            <th scope="col">Title</th>
                            <th scope="col">Section</th>
                            <th scope="col">Term</th>
                            <th scope="col">Seats</th>
                            <th scope="col">Status</th>
                            <th scope="col">Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {visible.length === 0 && (
                            <tr><td colSpan={7}>No course sections are available.</td></tr>
                        )}
                        {visible.map((course) => (
                            <tr key={course.id}>
                                <td>{course.code}</td>
                                <td>{course.title}</td>
                                <td>{course.sectionCode}</td>
                                <td>{course.term}</td>
                                <td>{course.availableSeats} of {course.capacity} available</td>
                                <td>
                                    <span className={`badge badge-${course.availability}`}>
                                        {AVAILABILITY_LABEL[course.availability]}
                                    </span>
                                </td>
                                <td>{actionFor(course)}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <h2 className="catalog-subheading">My Enrollments</h2>
            {myInTerm.length === 0 ? (
                <p className="catalog-note">You have not enrolled in any sections this term.</p>
            ) : (
                <ul className="catalog-mine">
                    {myInTerm.map((e) => (
                        <li key={e.id}>{e.code} {e.title} (Section {e.sectionCode})</li>
                    ))}
                </ul>
            )}
        </div>
    );
}
