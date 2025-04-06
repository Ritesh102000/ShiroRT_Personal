## 🔐 Face-Based Access Control with Google Drive Integration

This project demonstrates a **face recognition-based access control system** built using Flask, DeepFace, and Google Drive. The app authenticates users via facial recognition before allowing access to upload, view, and manage images stored in a linked Google Drive folder.

---

### 🧠 Face Recognition Overview

- Utilized a **pre-trained CNN model** (via [DeepFace](https://github.com/serengil/deepface)) for extracting facial **embeddings**.
- The model was trained using **positive and negative samples** to distinguish between known and unknown faces.
- After generating embeddings, we used **Singular Value Decomposition (SVD)** as a similarity measure to compare them. If similarity passes a threshold, the face is verified.
- New users can be automatically registered as known faces (up to 3) upon their first image submission, if their face is not recognized but is clearly detected.

---

### 👁️ Face Detection for Verification

1. User uploads a face image.
2. The system:
   - Compares it with existing known faces.
   - If match found: user is granted access.
   - If not and max known faces not reached: image is added as a new known face.
3. Face detection is powered by DeepFace’s internal model using `verify()` and `analyze()` functions.

---

### ☁️ Google Drive Integration

Once the user is verified, they are allowed to:

- **Upload images** to a connected **Google Drive folder** using the [PyDrive2](https://github.com/iterative/PyDrive2) library.
- View all uploaded images in a **gallery** (`/gallery` route).
- **Download** images via a secure proxy (`/download/<file_id>`).
- **Delete** selected files from the gallery (`/delete` route).

Google Drive credentials are managed with OAuth2 and cached in a local `mycreds.txt` file for seamless reuse.

---

### 📂 Folder Structure

- `static/captured/`: Stores uploaded face images temporarily.
- `static/known_faces/`: Stores registered known faces (max 3).
- `temp/`: Used for temporarily saving images during upload to Drive.

---

### ✅ Flow Summary

1. **User visits homepage** (`/`)
2. **Uploads a face image**
3. **System verifies identity** using face recognition
4. If verified:
   - Redirected to **gallery**
   - Can upload, view, download, or delete images in Google Drive
5. If not recognized and limit not reached:
   - User is **auto-registered** as a known face
6. If not verified and limit reached:
   - Access denied

---

This setup is ideal for scenarios where face-based verification is required before granting access to a secure content management platform.

