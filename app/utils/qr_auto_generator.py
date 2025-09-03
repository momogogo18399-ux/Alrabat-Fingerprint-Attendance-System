import sqlite3
import os
from app.utils.qr_manager import QRCodeManager
from app.database.database_manager import DatabaseManager

class QRAutoGenerator:
    """
    نظام توليد تلقائي لرموز QR لجميع الموظفين الموجودين
    """
    
    def __init__(self):
        self.qr_manager = QRCodeManager()
        self.db_manager = DatabaseManager()
    
    def add_qr_column_if_not_exists(self):
        """Add عمود qr_code إذا لم يكن موجوداً"""
        try:
            conn = sqlite3.connect("attendance.db")
            cursor = conn.cursor()
            
            # التحقق من وجود العمود
            cursor.execute("PRAGMA table_info(employees)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'qr_code' not in columns:
                print("Add عمود qr_code إلى جدول employees...")
                # Add العمود بدون UNIQUE أولاً
                cursor.execute("ALTER TABLE employees ADD COLUMN qr_code TEXT")
                conn.commit()
                
                # إنشاء فهرس منفصل للعمود
                try:
                    cursor.execute("CREATE UNIQUE INDEX idx_employees_qr_code ON employees(qr_code)")
                    conn.commit()
                    print("تم إنشاء فهرس فريد لعمود qr_code")
                except Exception as e:
                    print(f"Warning: لم يتم إنشاء فهرس فريد: {e}")
                
                print("تم Add عمود qr_code بنجاح")
            else:
                print("عمود qr_code موجود بالفعل")
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error في Add عمود qr_code: {e}")
            return False
    
    def generate_qr_for_all_employees(self):
        """إنشاء رموز QR لجميع الموظفين الذين لا يملكون رموز"""
        try:
            # Add العمود إذا لم يكن موجوداً
            if not self.add_qr_column_if_not_exists():
                return False
            
            # الحصول على جميع الموظفين
            employees = self.db_manager.get_all_employees()
            if not employees:
                print("لا يوجد موظفين في قاعدة البيانات")
                return False
            
            print(f"تم العثور على {len(employees)} موظف")
            
            success_count = 0
            error_count = 0
            
            for employee in employees:
                try:
                    # التحقق من وجود رمز QR
                    if not employee.get('qr_code'):
                        print(f"إنشاء رمز QR للموظف: {employee.get('name', 'غير معروف')}")
                        
                        # إنشاء رمز QR
                        qr_code = self.qr_manager.generate_qr_code(employee)
                        
                        if not qr_code:
                            print(f"❌ Failed في إنشاء رمز QR للموظف: {employee.get('name')}")
                            error_count += 1
                            continue
                        
                        # Save الرمز في قاعدة البيانات مباشرة
                        conn = sqlite3.connect("attendance.db")
                        cursor = conn.cursor()
                        
                        try:
                            cursor.execute("UPDATE employees SET qr_code = ? WHERE id = ?", (qr_code, employee['id']))
                            conn.commit()
                            success_count += 1
                            print(f"✅ تم إنشاء رمز QR للموظف: {employee.get('name')}")
                        except Exception as db_error:
                            print(f"❌ Error في قاعدة البيانات للموظف {employee.get('name')}: {db_error}")
                            error_count += 1
                        finally:
                            conn.close()
                    else:
                        print(f"الموظف {employee.get('name')} لديه رمز QR بالفعل")
                        
                except Exception as e:
                    error_count += 1
                    print(f"❌ Error في إنشاء رمز QR للموظف {employee.get('name')}: {e}")
            
            print(f"\n=== ملخص العملية ===")
            print(f"✅ تم إنشاء رموز QR بنجاح: {success_count}")
            print(f"❌ Failed في إنشاء رموز QR: {error_count}")
            print(f"📊 إجمالي الموظفين: {len(employees)}")
            
            return True
            
        except Exception as e:
            print(f"Error عام في توليد رموز QR: {e}")
            return False
    
    def regenerate_all_qr_codes(self):
        """إعادة إنشاء جميع رموز QR (Delete القديمة وإنشاء جديدة)"""
        try:
            print("⚠️ Warning: سيتم Delete جميع رموز QR الموجودة وإنشاء رموز جديدة")
            confirm = input("هل تريد المتابعة؟ (y/n): ")
            
            if confirm.lower() != 'y':
                print("تم Cancel العملية")
                return False
            
            # Add العمود إذا لم يكن موجوداً
            if not self.add_qr_column_if_not_exists():
                return False
            
            # Delete جميع رموز QR الموجودة
            conn = sqlite3.connect("attendance.db")
            cursor = conn.cursor()
            cursor.execute("UPDATE employees SET qr_code = NULL")
            conn.commit()
            conn.close()
            
            print("تم Delete جميع رموز QR القديمة")
            
            # إنشاء رموز جديدة
            return self.generate_qr_for_all_employees()
            
        except Exception as e:
            print(f"Error في إعادة إنشاء رموز QR: {e}")
            return False
    
    def verify_qr_codes(self):
        """التحقق من صحة جميع رموز QR الموجودة"""
        try:
            employees = self.db_manager.get_all_employees()
            if not employees:
                print("لا يوجد موظفين للتحقق")
                return False
            
            valid_count = 0
            invalid_count = 0
            
            for employee in employees:
                qr_code = employee.get('qr_code')
                if qr_code:
                    # التحقق من صحة الرمز
                    result = self.qr_manager.verify_qr_code(qr_code)
                    if result and result.get('is_valid'):
                        valid_count += 1
                    else:
                        invalid_count += 1
                        print(f"❌ رمز QR غير صالح للموظف: {employee.get('name')}")
                else:
                    invalid_count += 1
                    print(f"❌ لا يوجد رمز QR للموظف: {employee.get('name')}")
            
            print(f"\n=== نتائج التحقق ===")
            print(f"✅ رموز QR صالحة: {valid_count}")
            print(f"❌ رموز QR غير صالحة: {invalid_count}")
            print(f"📊 إجمالي الموظفين: {len(employees)}")
            
            return valid_count == len(employees)
            
        except Exception as e:
            print(f"Error في التحقق من رموز QR: {e}")
            return False

def main():
    """الدالة الرئيسية للتشغيل"""
    print("🚀 نظام توليد رموز QR التلقائي")
    print("=" * 50)
    
    generator = QRAutoGenerator()
    
    while True:
        print("\nاختر العملية:")
        print("1. إنشاء رموز QR للموظفين الجدد")
        print("2. إعادة إنشاء جميع رموز QR")
        print("3. التحقق من صحة رموز QR")
        print("4. خروج")
        
        choice = input("\nاختيارك (1-4): ")
        
        if choice == '1':
            print("\nإنشاء رموز QR للموظفين الجدد...")
            generator.generate_qr_for_all_employees()
            
        elif choice == '2':
            print("\nإعادة إنشاء جميع رموز QR...")
            generator.regenerate_all_qr_codes()
            
        elif choice == '3':
            print("\nالتحقق من صحة رموز QR...")
            generator.verify_qr_codes()
            
        elif choice == '4':
            print("شكراً لاستخدام النظام!")
            break
            
        else:
            print("اختيار غير صحيح، يرجى المحاولة مرة أخرى")

if __name__ == "__main__":
    main()
